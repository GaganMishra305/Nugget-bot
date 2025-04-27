# doc string have been used to clarify the usage

import chromadb
import json
import os
import uuid
import shutil
from typing import Dict, List, Any, Optional, Tuple

class Vectorizer:
    def process_restaurant_data(self, json_files_path: str, restaurant_collection, menu_item_collection) -> None:
        """
        Process restaurant data from JSON files and add to ChromaDB collections
        
        Args:
            json_files_path: Directory containing restaurant JSON files
            restaurant_collection: ChromaDB collection for restaurant data
            menu_item_collection: ChromaDB collection for menu item data
        """
        if not os.path.exists(json_files_path):
            print(f"Error: Directory {json_files_path} not found!")
            return
            
        processed_restaurants = 0
        all_locations = set()
        
        # Process each JSON file
        for filename in os.listdir(json_files_path):
            if filename.endswith('.json'):
                file_path = os.path.join(json_files_path, filename)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Sanitize data to handle None values
                    sanitized_data = self.sanitize_restaurant_data(data)
                    
                    # Extract location
                    location = self.extract_location(sanitized_data['basic_info']['address'])
                    all_locations.add(location)
                    
                    # Add to database
                    self.add_restaurant_to_db(sanitized_data, restaurant_collection, menu_item_collection)
                    
                    processed_restaurants += 1
                    print(f"Processed {filename}")
                    
                except Exception as e:
                    print(f"Error processing {filename}: {str(e)}")
                    import traceback
                    traceback.print_exc()
        
        print(f"Successfully indexed {processed_restaurants} restaurants")
        print(f"Locations covered: {', '.join(sorted(all_locations))}")


    def sanitize_restaurant_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and sanitize restaurant data to prevent None values
        
        Args:
            data: Raw restaurant data from JSON
        Returns:
            Sanitized restaurant data
        """
        # Make a deep copy to avoid modifying the original
        sanitized = json.loads(json.dumps(data))
        
        # Sanitize basic info
        if 'basic_info' in sanitized:
            for key in sanitized['basic_info']:
                if sanitized['basic_info'][key] is None:
                    if key in ['rating']:
                        sanitized['basic_info'][key] = 0
                    else:
                        sanitized['basic_info'][key] = ''
        
        # Sanitize menu items
        if 'menu' in sanitized:
            for category in sanitized['menu']:
                for i, item in enumerate(sanitized['menu'][category]):
                    for key in item:
                        if item[key] is None:
                            if key in ['price']:
                                sanitized['menu'][category][i][key] = 0
                            elif key in ['veg_status']:
                                sanitized['menu'][category][i][key] = 'unknown'
                            else:
                                sanitized['menu'][category][i][key] = ''
        
        return sanitized


    def add_restaurant_to_db(self, restaurant_data: Dict[str, Any], restaurant_collection, menu_item_collection) -> None:
        """
        Add a restaurant and its menu items to ChromaDB
        
        Args:
            restaurant_data: JSON data for a restaurant
            restaurant_collection: ChromaDB collection for restaurant data
            menu_item_collection: ChromaDB collection for menu item data
        """
        # Extract basic info
        restaurant_name = restaurant_data['basic_info']['name']
        restaurant_id = str(uuid.uuid4())
        location = self.extract_location(restaurant_data['basic_info']['address'])
        
        # Create restaurant document text for embedding
        restaurant_text = f"{restaurant_name} is a restaurant located in {location}. "
        
        if 'rating' in restaurant_data['basic_info'] and restaurant_data['basic_info']['rating'] is not None:
            restaurant_text += f"It has a rating of {restaurant_data['basic_info']['rating']}. "
        
        if 'special_info' in restaurant_data['basic_info'] and restaurant_data['basic_info']['special_info'] is not None:
            restaurant_text += f"{restaurant_data['basic_info']['special_info']}. "
        
        if 'operating_hours' in restaurant_data['basic_info'] and restaurant_data['basic_info']['operating_hours'] is not None:
            restaurant_text += f"Operating hours: {restaurant_data['basic_info']['operating_hours']}. "
        
        # Prepare metadata with None value handling
        metadata = {
            "name": restaurant_name,
            "location": location,
            "address": restaurant_data['basic_info']['address'],
            "rating": restaurant_data['basic_info'].get('rating', 0) or 0,  # Replace None with 0
            "contact": restaurant_data['basic_info'].get('contact', '') or '',  # Replace None with empty string
            "operating_hours": restaurant_data['basic_info'].get('operating_hours', '') or '',
            "type": "restaurant"
        }
        
        # Add restaurant to collection
        restaurant_collection.add(
            ids=[restaurant_id],
            documents=[restaurant_text],
            metadatas=[metadata]
        )
        
        # Process menu items
        for category, items in restaurant_data['menu'].items():
            for item in items:
                self.add_menu_item_to_db(item, category, restaurant_id, restaurant_name, menu_item_collection)


    def add_menu_item_to_db(self, item: Dict[str, Any], category: str, restaurant_id: str, restaurant_name: str, menu_item_collection) -> None:
        """
        Add a menu item to ChromaDB
        
        Args:
            item: Menu item data
            category: Menu category
            restaurant_id: Parent restaurant ID
            restaurant_name: Parent restaurant name
            menu_item_collection: ChromaDB collection for menu item data
        """
        item_id = str(uuid.uuid4())
        
        # Handle potential None in veg_status
        veg_status = item.get('veg_status', 'unknown')
        if veg_status is None:
            veg_status = 'unknown'
        
        item_text = f"{item['name']} is a {veg_status} item "
        item_text += f"in the {category} category at {restaurant_name}. "
        
        # Handle potential None in price
        price = item.get('price', 0)
        if price is None:
            price = 0
        
        if price > 0:
            item_text += f"It costs ₹{price}. "
        
        # Handle potential None in description
        description = item.get('description', '')
        if description and description is not None:
            item_text += f"Description: {description}. "
        
        # Define price range
        price_range = "budget"
        if price > 300:
            price_range = "premium"
        elif price > 150:
            price_range = "moderate"
        
        # Prepare metadata with None value handling
        metadata = {
            "name": item['name'],
            "category": category,
            "restaurant_id": restaurant_id,
            "restaurant_name": restaurant_name,
            "price": price,
            "price_range": price_range,
            "veg_status": veg_status,
            "type": "menu_item"
        }
        
        # Add menu item to collection
        menu_item_collection.add(
            ids=[item_id],
            documents=[item_text],
            metadatas=[metadata]
        )


    def extract_location(self, address: str) -> str:
        """
        Extract city/area from address
        
        Args:
            address: Full address string
        
        Returns:
            Location/area name
        """
        parts = address.split(',')
        if len(parts) >= 2:
            return parts[0].strip()
        return address.strip()


    def search_restaurants(self, query: str, restaurant_collection, location: Optional[str] = None, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Search for restaurants matching the query
        
        Args:
            query: Search text
            restaurant_collection: ChromaDB collection for restaurant data
            location: Optional location filter
            limit: Maximum number of results
            
        Returns:
            List of matching restaurant metadata
        """
        where_clause = {"type": "restaurant"}
        
        if location:
            where_clause["location"] = location
        
        results = restaurant_collection.query(
            query_texts=[query],
            n_results=limit,
            where=where_clause
        )
        
        # Format the results
        formatted_results = []
        for i in range(len(results['ids'][0])):
            formatted_results.append(results['metadatas'][0][i])
        
        return formatted_results


    def search_dishes(self, query: str, menu_item_collection, veg_only: bool = False, 
                    price_range: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for menu items matching the query
        
        Args:
            query: Search text
            menu_item_collection: ChromaDB collection for menu item data
            veg_only: Filter for vegetarian items only
            price_range: Optional price range filter ('budget', 'moderate', 'premium')
            limit: Maximum number of results
            
        Returns:
            List of matching menu item metadata
        """
        where_clause = {"type": "menu_item"}
        
        if veg_only:
            where_clause["veg_status"] = "veg"
        
        if price_range:
            where_clause["price_range"] = price_range
        
        results = menu_item_collection.query(
            query_texts=[query],
            n_results=limit,
            where=where_clause
        )
        
        # Format the results
        formatted_results = []
        for i in range(len(results['ids'][0])):
            formatted_results.append(results['metadatas'][0][i])
        
        return formatted_results


    def compare_restaurants(self, restaurant_names: List[str], restaurant_collection, 
                            menu_item_collection, aspect: str = "rating") -> List[Dict[str, Any]]:
        """
        Compare restaurants based on a specific aspect
        
        Args:
            restaurant_names: List of restaurant names to compare
            restaurant_collection: ChromaDB collection for restaurant data
            menu_item_collection: ChromaDB collection for menu item data
            aspect: Aspect to compare ('rating', 'menu_variety', etc.)
            
        Returns:
            Comparison results sorted by the specified aspect
        """
        results = []
        
        for name in restaurant_names:
            # Find the restaurant by name
            restaurant_results = restaurant_collection.query(
                query_texts=[name],
                n_results=1
            )
            
            if len(restaurant_results['ids'][0]) > 0:
                restaurant_id = restaurant_results['ids'][0][0]
                restaurant_metadata = restaurant_results['metadatas'][0][0]
                
                # Get menu items for this restaurant
                menu_results = menu_item_collection.query(
                    query_texts=[""],  # Empty query to match all
                    n_results=100,     # Get many items
                    where={"restaurant_name": restaurant_metadata['name']}
                )
                
                # Calculate metrics
                menu_count = len(menu_results['ids'][0])
                veg_count = sum(1 for i in range(menu_count) 
                            if menu_results['metadatas'][0][i]['veg_status'] == 'veg')
                
                avg_price = 0
                if menu_count > 0:
                    avg_price = sum(menu_results['metadatas'][0][i]['price'] for i in range(menu_count)) / menu_count
                
                # Add to results
                results.append({
                    "name": restaurant_metadata['name'],
                    "rating": restaurant_metadata.get('rating', 0),
                    "menu_count": menu_count,
                    "veg_percentage": (veg_count / menu_count * 100) if menu_count > 0 else 0,
                    "avg_price": avg_price
                })
        
        # Sort by the requested aspect
        if aspect in ["rating", "menu_count", "veg_percentage", "avg_price"]:
            results.sort(key=lambda x: x[aspect], reverse=True)
        
        return results


    def find_restaurants_for_dietary_needs(self, dietary_preference: str, menu_item_collection,
                                        restaurant_collection, location: Optional[str] = None, 
                                        limit: int = 3) -> List[Dict[str, Any]]:
        """
        Find restaurants suitable for specific dietary needs
        
        Args:
            dietary_preference: Dietary preference (e.g., 'vegetarian')
            menu_item_collection: ChromaDB collection for menu item data
            restaurant_collection: ChromaDB collection for restaurant data
            location: Optional location filter
            limit: Maximum number of results
            
        Returns:
            List of suitable restaurants with their vegetarian options
        """
        veg_status = "veg" if "veg" in dietary_preference.lower() else "non-veg"
        
        # First, find menu items matching the dietary preference
        where_clause = {"veg_status": veg_status}
        
        menu_results = menu_item_collection.query(
            query_texts=[dietary_preference],
            n_results=50,  # Get many items
            where=where_clause
        )
        
        # Group by restaurant
        restaurant_items = {}
        for i in range(len(menu_results['ids'][0])):
            restaurant_name = menu_results['metadatas'][0][i]['restaurant_name']
            
            if restaurant_name not in restaurant_items:
                restaurant_items[restaurant_name] = []
                
            restaurant_items[restaurant_name].append(menu_results['metadatas'][0][i])
        
        # Sort restaurants by number of matching items
        sorted_restaurants = sorted(restaurant_items.items(), 
                                key=lambda x: len(x[1]), 
                                reverse=True)
        
        # Format results
        results = []
        for restaurant_name, items in sorted_restaurants[:limit]:
            # Get restaurant details
            restaurant_results = restaurant_collection.query(
                query_texts=[restaurant_name],
                n_results=1
            )
            
            if len(restaurant_results['ids'][0]) > 0:
                restaurant_metadata = restaurant_results['metadatas'][0][0]
                
                # Only include if location matches (if specified)
                if location and location.lower() not in restaurant_metadata['location'].lower():
                    continue
                    
                results.append({
                    "restaurant": restaurant_metadata,
                    "matching_items": items[:5]  # Show top 5 matching items
                })
        
        return results

    ## QUERY TESTER FUNCTION
    def test_queries(self, restaurant_collection, menu_item_collection) -> None:
        """
        Test various query types on the vector database
        
        Args:
            restaurant_collection: ChromaDB collection for restaurant data
            menu_item_collection: ChromaDB collection for menu item data
        """
        print("\n=== Testing Restaurant Search ===")
        results = restaurant_collection.query(
            query_texts=["popular restaurants"],
            n_results=3
        )
        
        print(f"Found {len(results['ids'][0])} matching restaurants:")
        for i in range(len(results['ids'][0])):
            print(f"- {results['metadatas'][0][i]['name']} in {results['metadatas'][0][i]['location']}")
        
        print("\n=== Testing Menu Item Search ===")
        results = menu_item_collection.query(
            query_texts=["tandoori dishes"],
            n_results=5
        )
        
        print(f"Found {len(results['ids'][0])} matching menu items:")
        for i in range(len(results['ids'][0])):
            metadata = results['metadatas'][0][i]
            print(f"- {metadata['name']} at {metadata['restaurant_name']} (₹{metadata['price']})")
        
        print("\n=== Testing Vegetarian Filter ===")
        results = menu_item_collection.query(
            query_texts=["vegetarian food"],
            n_results=5,
            where={"veg_status": "veg"}
        )
        
        print(f"Found {len(results['ids'][0])} matching vegetarian items:")
        for i in range(len(results['ids'][0])):
            metadata = results['metadatas'][0][i]
            print(f"- {metadata['name']} at {metadata['restaurant_name']} (₹{metadata['price']})")
        
        print("\n=== Testing Price Range Filter ===")
        results = menu_item_collection.query(
            query_texts=["affordable food"],
            n_results=5,
            where={"price_range": "budget"}
        )
        
        print(f"Found {len(results['ids'][0])} budget-friendly items (₹0-150):")
        for i in range(len(results['ids'][0])):
            metadata = results['metadatas'][0][i]
            print(f"- {metadata['name']} at {metadata['restaurant_name']} (₹{metadata['price']})")
        
        # Demonstrate advanced query utility functions
        print("\n=== Restaurant Comparison ===")
        restaurants = restaurant_collection.query(
            query_texts=[""],
            n_results=2
        )
        
        if len(restaurants['ids'][0]) >= 2:
            restaurant1 = restaurants['metadatas'][0][0]['name']
            restaurant2 = restaurants['metadatas'][0][1]['name']
            results = self.compare_restaurants([restaurant1, restaurant2], restaurant_collection, menu_item_collection)
            
            print(f"Comparing {restaurant1} vs {restaurant2}:")
            for restaurant in results:
                print(f"- {restaurant['name']}: Rating: {restaurant['rating']}, " +
                    f"Avg Price: ₹{restaurant['avg_price']:.2f}, " +
                    f"Veg Options: {restaurant['veg_percentage']:.1f}%")


    def main(self):
        # Define paths
        json_files_path = "../public/scraped_data"
        persist_directory = "./restaurant_vector_db"
        
        # Check if the vector DB directory exists
        if os.path.exists(persist_directory) and os.path.isdir(persist_directory):
            delete_db = input(f"Vector database already exists at {persist_directory}. Delete it? (y/n): ").lower() == 'y'
            if delete_db:
                shutil.rmtree(persist_directory)
                print(f"Deleted existing database at {persist_directory}")
                
                # Create new client and collections
                client = chromadb.PersistentClient(path=persist_directory)
                restaurant_collection = client.create_collection("restaurants")
                menu_item_collection = client.create_collection("menu_items")
                
                # Process restaurant data
                self.process_restaurant_data(json_files_path, restaurant_collection, menu_item_collection)
            else:
                # Use existing database
                client = chromadb.PersistentClient(path=persist_directory)
                try:
                    restaurant_collection = client.get_collection("restaurants")
                    menu_item_collection = client.get_collection("menu_items")
                    print(f"Using existing database with {restaurant_collection.count()} restaurants and {menu_item_collection.count()} menu items")
                except ValueError as e:
                    print(f"Error accessing collections: {e}")
                    return
        else:
            # Create new database
            print("Creating new vector database...")
            client = chromadb.PersistentClient(path=persist_directory)
            restaurant_collection = client.create_collection("restaurants")
            menu_item_collection = client.create_collection("menu_items")
            
            # Process restaurant data
            self.process_restaurant_data(json_files_path, restaurant_collection, menu_item_collection)
        
        # Test the database
        self.test_queries(restaurant_collection, menu_item_collection)


vectorDBmaker = Vectorizer()
vectorDBmaker.main()