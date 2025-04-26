import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import os

# This class is responsible for scraping restaurant data from Justdial
class RestaurantScraper:
    def extract_menu(self, soup):
        menu_dict = {}
        menu_sections = soup.find_all('div', class_='accordion_collapse')
        
        for section in menu_sections:
            category = section.get('aria-labelledby', 'Unknown')
            items = []
            menu_items = section.find_all('div', class_='service_preview')
            
            for item in menu_items:
                try:
                    item_data = {
                        "name": None,
                        "price": None,
                        "veg_status": None
                    }
                    name_elem = item.find('div', class_='service_name')
                    if name_elem:
                        link = name_elem.find('a')
                        if link:
                            item_data["name"] = link.text.strip()
                        else:
                            item_data["name"] = name_elem.text.strip()
                    
                    price_elem = item.find('div', class_='service_priceoffer')
                    if price_elem:
                        price_text = price_elem.text.strip()
                        item_data["price"] = int(price_text.split('₹')[1].strip())
                    
                    veg_img = item.find('img', alt='Veg')
                    nonveg_img = item.find('img', alt='Non Veg')
                    if veg_img:
                        item_data["veg_status"] = "veg"
                    elif nonveg_img:
                        item_data["veg_status"] = "non-veg"
                    
                    if item_data["name"]:
                        items.append(item_data)
                        
                except Exception as e:
                    print(f"Error processing item: {str(e)}")
                    continue
            
            menu_dict[category] = items
        return menu_dict

    def create_restaurant_json(self, soup, url):
        """Create a complete restaurant data JSON with all scraped information"""
        restaurant_data = {
            "scrape_metadata": {
                "scrape_url": url,
                "scrape_timestamp": datetime.now().isoformat()
            },
            "basic_info": {
                "name": None,
                "rating": None,
                "rating_count": None,
                "address": None,
                "contact": None,
                "operating_hours": None,
                "special_info": None
            },
            "menu": {}
        }
        
        try:
            # Basic Info
            name_elem = soup.find('div', class_='compney')
            if name_elem:
                restaurant_data["basic_info"]["name"] = name_elem.text.strip()
                
            rating_elem = soup.find('div', class_='vendbox_rateavg')
            if rating_elem:
                restaurant_data["basic_info"]["rating"] = float(rating_elem.text.strip())
                
            rate_count_elem = soup.find('div', class_='vendbox_ratecount')
            if rate_count_elem:
                restaurant_data["basic_info"]["rating_count"] = rate_count_elem.text.split(' ')[0]
                
            address_elem = soup.find('div', class_='adress').find_next('a')
            if address_elem:
                restaurant_data["basic_info"]["address"] = address_elem.text.strip()
            
            # Contact
            restaurant_data["basic_info"]["contact"] = "07947114254"  # As given in the notebook
            
            # Operating Hours
            hours_elem = soup.find_all('div', class_='operation')
            if len(hours_elem) > 1:
                restaurant_data["basic_info"]["operating_hours"] = hours_elem[1].text.strip()
                
            # Special Info
            special_info_elem = soup.find_all('div', 'adress font14 fw100 color111')
            if len(special_info_elem) > 1:
                restaurant_data["basic_info"]["special_info"] = special_info_elem[1].text.strip()
            
            # Menu (using existing extract_menu function)
            menu_data = self.extract_menu(soup)
            if menu_data:
                restaurant_data["menu"] = menu_data
                
            # Save to JSON file
            filename = f"scraped_data/{name_elem.text.strip()}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(restaurant_data, f, indent=2, ensure_ascii=False)
                
            return restaurant_data
            
        except Exception as e:
            print(f"Error creating restaurant JSON: {str(e)}")
            return None


    def scrape_restaurant(self, url):
        def get_headers():
            return {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
            }

        # Make request with proper headers
        response = requests.get(url, headers=get_headers())
        response.raise_for_status()

        # Parse HTML
        soup = BeautifulSoup(response.text, 'lxml')

        # call the scraper
        restaurant_data = self.create_restaurant_json(soup, url)
        if restaurant_data:
            print(f"Scraped data for {restaurant_data['basic_info']['name']}")
        else:
            print("Failed to scrape restaurant data.")

# This class helps to interact with the above class by using two modes.
# 1. Interactive Mode: For scraping a single restaurant provided by the user
# 2. Update Mode: For scraping multiple restaurants from a list
class RunningModes:
    def __init__(self):
        self.scraper = RestaurantScraper()
        # Create scraped_data directory if it doesn't exist
        if not os.path.exists('scraped_data'):
            os.makedirs('scraped_data')
            
    def get_headers(self):
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }

    def scrape_single_restaurant(self, url, contact_no=None):
        """Scrape a single restaurant"""
        try:
            response = requests.get(url, headers=self.get_headers())
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Modify create_restaurant_json call to include contact_no
            restaurant_data = self.scraper.create_restaurant_json(soup, url)
            if restaurant_data and contact_no:
                restaurant_data["basic_info"]["contact"] = contact_no
                
                # Re-save the file with updated contact
                filename = f"scraped_data/{restaurant_data['basic_info']['name']}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(restaurant_data, f, indent=2, ensure_ascii=False)
            
            return restaurant_data
            
        except Exception as e:
            print(f"Error scraping restaurant: {str(e)}")
            return None

    def interactive_mode(self):
        """Interactive mode for scraping a single restaurant"""
        print("\n=== Interactive Mode ===")
        while True:
            url = input("\nEnter Justdial restaurant URL (or 'exit' to quit): ")
            if url.lower() == 'exit':
                break
                
            print("\nScraping restaurant...")
            restaurant_data = self.scrape_single_restaurant(url)
            
            if restaurant_data:
                print(f"\n✓ Successfully scraped: {restaurant_data['basic_info']['name']}")
                print(f"Data saved to: scraped_data/{restaurant_data['basic_info']['name']}.json")
            else:
                print("\n✗ Failed to scrape restaurant")
                
            again = input("\nScrape another restaurant? (y/n): ")
            if again.lower() != 'y':
                break

    def update_mode(self, restaurant_list):
        """Update mode for scraping multiple restaurants from a list"""
        print("\n=== Update Mode ===")
        print(f"Found {len(restaurant_list)} restaurants to scrape")
        
        successful = 0
        failed = 0
        
        for restaurant in restaurant_list:
            print(f"\nScraping {restaurant['name']}...")
            
            data = self.scrape_single_restaurant(
                restaurant['url'], 
                contact_no=restaurant['contact_no']
            )
            
            if data:
                successful += 1
                print(f"✓ Successfully scraped: {restaurant['name']}")
            else:
                failed += 1
                print(f"✗ Failed to scrape: {restaurant['name']}")
        
        print(f"\nScraping Complete!")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Total: {len(restaurant_list)}")


# THESE ARE THE TARGET RESTAURANTS
target_restaurants = [
    {
        "name"  : "Sharma Ji Ki Chai",
        "url": "https://www.justdial.com/Lucknow/Sharma-Ji-Ki-Chai-Near-novality-cinema-Hazratganj/0522PX522-X522-160826112726-G6H1_BZDET/menu?trkid=277-remotecity-fcat&term=Restaurants&ncatid=10408936&area=&search=Best%20Restaurants%20in%20Lucknow%20-%20Order%20Food%20Online&mncatname=Restaurants&abd_btn=&abd_heading=&bd=1&cat_b2b_flag=0&searchfrom=lst",
        "contact_no" :  "07947109049"
    },
    {
        "name" : "Tunday Kababi",
        "url" : "https://www.justdial.com/Lucknow/Tunday-Kababi-Beside-StMarry-Inter-College-Neer-Around-Town-Aminabad/0522PX522-X522-101028105411-T9G7_BZDET/menu?trkid=277-remotecity-fcat&term=Restaurants&ncatid=10408936&area=&search=Best%20Restaurants%20in%20Lucknow%20-%20Order%20Food%20Online&mncatname=Restaurants&abd_btn=&abd_heading=&bd=1&cat_b2b_flag=0&searchfrom=lst",
        "contact_no" :  "07942693231"
    },
    {
        "name"  : "Milan A Speciality Restaurant",
        "url"   :  "https://www.justdial.com/Lucknow/Milan-A-Speciality-Restaurant-Opposite-Railway-Station-Charbagh/0522PX522-X522-110304200136-G5H7_BZDET/menu?trkid=277-remotecity-fcat&term=Restaurants&ncatid=10408936&area=&search=Best%20Restaurants%20in%20Lucknow%20-%20Order%20Food%20Online&mncatname=Restaurants&abd_btn=&abd_heading=&bd=1&cat_b2b_flag=0&searchfrom=lst",
        "contact_no" :  "07942689078"
    },
    {
        "name"  : "Moti Mahal Restaurant",
        "url"   : "https://www.justdial.com/Lucknow/Moti-Mahal-Restaurant-Next-Central-Bank-Of-India-Near-Hanuman-Mandir-Opposite-Multi-Level-Parking-Hazratganj/0522P522STDS000110_BZDET/menu?trkid=277-remotecity-fcat&term=Restaurants&ncatid=10408936&area=&search=Best%20Restaurants%20in%20Lucknow%20-%20Order%20Food%20Online&mncatname=Restaurants&abd_btn=&abd_heading=&bd=1&cat_b2b_flag=0&searchfrom=lst",
        "contact_no" :  "07947137089"
    },
    {
        "name" : "Colours By Royal Cafe",
        "url": "https://www.justdial.com/Lucknow/Colours-By-Royal-Cafe-Opposite-Sahara-Ganj-Mall-Hazratganj/0522PX522-X522-171223163048-Y9E7_BZDET/menu?trkid=277-remotecity-fcat&term=Restaurants&ncatid=10408936&area=&search=Best%20Restaurants%20in%20Lucknow%20-%20Order%20Food%20Online&mncatname=Restaurants&abd_btn=&abd_heading=&bd=1&cat_b2b_flag=0&searchfrom=lst"  ,   
        "contact_no" :  "07947111398"
    },
    {
        "name" : "Barbeque Nation",
        "url" : "https://www.justdial.com/Lucknow/Barbeque-Nation-Vipin-Khand-Gomti-Nagar/0522PX522-X522-130329165812-U5P6_BZDET/menu?trkid=277-remotecity-fcat&term=Restaurants&ncatid=10408936&area=&search=Best%20Restaurants%20in%20Lucknow%20-%20Order%20Food%20Online&mncatname=Restaurants&abd_btn=&abd_heading=&bd=1&cat_b2b_flag=0&searchfrom=lst",
        "contact_no" :  "07947148142"
    },
    {
        "name" : "Mashi Biryani World",
        "url" : "https://www.justdial.com/Lucknow/Mashi-Biryani-World-Behind-Neebu-Park-Bada-Imambada-Oppo-Khunkhun-Ji-Lucknow-Chowk/0522PX522-X522-160705173620-S6L4_BZDET/menu?trkid=277-remotecity-fcat&term=Restaurants&ncatid=10408936&area=&search=Best%20Restaurants%20in%20Lucknow%20-%20Order%20Food%20Online&mncatname=Restaurants&abd_btn=&abd_heading=&bd=1&cat_b2b_flag=0&searchfrom=lst",
        "contact_no" :  "07947138467"
    }
]

def main():
    modes = RunningModes()
    
    while True:
        print("\n=== Restaurant Scraper ===")
        print("1. Interactive Mode (Single Restaurant)")
        print("2. Update Mode (Multiple Restaurants)")
        print("3. Exit")
        
        choice = input("\nSelect mode (1-3): ")
        
        if choice == '1':
            modes.interactive_mode()
        elif choice == '2':
            modes.update_mode(target_restaurants)
        elif choice == '3':
            print("\nGoodbye!")
            break
        else:
            print("\nInvalid choice. Please try again.")

if __name__ == "__main__":
    main()