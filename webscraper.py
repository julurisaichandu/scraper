import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import random
import json
import logging
from bs4 import BeautifulSoup
from seleniumbase import Driver
# BaseCase.main(__name__, __file__)


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='linkedin_scraper.log'
)

class LinkedInScraper:
    def __init__(self):
        self.driver = None
        self.wait = None
        
    def _random_delay(self, min_delay=2, max_delay=5):
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)

    def start_browser(self):
        try:
            # self.driver = uc.Chrome()
            self.driver = Driver(uc=True)
            self.wait = WebDriverWait(self.driver, 10)
        except Exception as e:
            logging.error(f"Failed to start browser: {str(e)}")
            raise

    def login_to_linkedin(self, username, password):
        try:
            self.driver.get('https://www.linkedin.com/login')
            self._random_delay(3, 6)
            
            username_field = self.wait.until(EC.presence_of_element_located((By.ID, 'username')))
            password_field = self.wait.until(EC.presence_of_element_located((By.ID, 'password')))
            
            for char in username:
                username_field.send_keys(char)
                time.sleep(random.uniform(0.1, 0.3))
            
            for char in password:
                password_field.send_keys(char)
                time.sleep(random.uniform(0.1, 0.3))
            
            self._random_delay(1, 2)
            password_field.submit()
            self._random_delay(3, 5)
            
        except Exception as e:
            logging.error(f"Login failed: {str(e)}")
            raise

    def scrape_profile(self, profile_url):
        try:
            self.driver.get(profile_url)
            self._random_delay(4, 7)
            
            # Scroll slowly
            total_height = int(self.driver.execute_script("return document.body.scrollHeight"))
            # for i in range(1, total_height, random.randint(100, 300)):
            #     self.driver.execute_script(f"window.scrollTo(0, {i});")
            #     time.sleep(random.uniform(0.1, 0.3))
            
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            profile_data = {}
            
            # Basic Information
            name = soup.find('h1', {'class': 'text-heading-xlarge inline t-24 v-align-middle break-words'})
            profile_data['name'] = name.get_text().strip() if name else ""
            profile_data['url'] = profile_url
            
            headline = soup.find('div', {'class': 'text-body-medium break-words'})
            profile_data['headline'] = headline.get_text().strip() if headline else ""

            print("got the name, url and headline")
            
            # About Section
            try:
                # self.driver.find_element(By.CLASS_NAME, "inline-show-more-text__button").click()
                self._random_delay(1, 2)
                page_source = self.driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                about = soup.find('div', {'class': 'display-flex ph5 pv3'})
                profile_data['about'] = about.get_text().strip() if about else ""
                print("got about data")
            except:
                profile_data['about'] = ""
                print("about is null or some error parsing")


            # Experience Section
            profile_data['experience'] = self._extract_experience(soup)
            
            # Education Section
            profile_data['education'] = self._extract_education(soup)
            
            # Licenses Section
            profile_data['licenses'] = self._extract_licenses()
            
            return profile_data
            
        except Exception as e:
            logging.error(f"Failed to scrape profile {profile_url}: {str(e)}")
            return None

    def _extract_experience(self, soup):
        print("extracting experience")
        experience_list = []
        sections = soup.find_all('section', {'class': 'artdeco-card pv-profile-card break-words mt2'})
        print("extracting sections")
        
        for section in sections:
            if section.find('div', {'id': 'experience'}):
                items = section.find_all('div', {'class': 'kxYaWHyWofucTGWMCDhTqvkdVrutyFrdCs aHMQxlljzRApJvLPsmPIqnqBmfVufooqg DGzSNKvwJDowmzuYPEImSXtCyTZWFdmtrztU'})
                
                for item in items:
                    exp_dict = {}
                    name_elem = item.find('div', {'class': 'display-flex flex-wrap align-items-center full-height'})
                    if name_elem and name_elem.find('span', {'class': 'visually-hidden'}):
                        exp_dict['company_name'] = name_elem.find('span', {'class': 'visually-hidden'}).get_text().strip()
                    
                    positions = item.find_all('div', {'class': 'kxYaWHyWofucTGWMCDhTqvkdVrutyFrdCs'})
                    position_list = []
                    
                    for position in positions:
                        spans = position.find_all('span', {'class': 'visually-hidden'})
                        if len(spans) >= 3:
                            position_dict = {
                                'designation': spans[0].get_text().strip(),
                                'duration': spans[1].get_text().strip(),
                                'location': spans[2].get_text().strip()
                            }
                            position_list.append(position_dict)
                    
                    exp_dict['positions'] = position_list
                    experience_list.append(exp_dict)
        
        return experience_list

    def _extract_education(self, soup):
        education_list = []
        sections = soup.find_all('section', {'class': 'artdeco-card pv-profile-card break-words mt2'})
        
        for section in sections:
            if section.find('div', {'id': 'education'}):
                items = section.find_all('div', {'class': 'kxYaWHyWofucTGWMCDhTqvkdVrutyFrdCs aHMQxlljzRApJvLPsmPIqnqBmfVufooqg DGzSNKvwJDowmzuYPEImSXtCyTZWFdmtrztU'})
                
                for item in items:
                    spans = item.find_all('span', {'class': 'visually-hidden'})
                    if len(spans) >= 3:
                        edu_dict = {
                            'college': spans[0].get_text().strip(),
                            'degree': spans[1].get_text().strip(),
                            'duration': spans[2].get_text().strip()
                        }
                        education_list.append(edu_dict)
        
        return education_list

    def _extract_licenses(self):
        licenses_list = []
        try:
            # Click to open the licenses section
            self.driver.click("#navigation-index-see-all-licenses-and-certifications")
            
            # Wait for the section to load by targeting a specific element in the expanded section
            # WebDriverWait(self.driver, 10).until(
            #     EC.presence_of_element_located((By.CLASS_NAME, "artdeco-card pb3"))
            # )
            
            self._random_delay(2, 3)
            
            # Parse the page content with BeautifulSoup
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            section = soup.find('section', {'class': 'artdeco-card pb3'})
            
            if section:
                items = section.find_all('div', {
                    'class': 'kxYaWHyWofucTGWMCDhTqvkdVrutyFrdCs aHMQxlljzRApJvLPsmPIqnqBmfVufooqg DGzSNKvwJDowmzuYPEImSXtCyTZWFdmtrztU'
                })
                
                for item in items:
                    spans = item.find_all('span', {'class': 'visually-hidden'})
                    if len(spans) >= 3:
                        license_dict = {
                            'name': spans[0].get_text().strip(),
                            'institute': spans[1].get_text().strip(),
                            'issued_date': spans[2].get_text().strip()
                        }
                        licenses_list.append(license_dict)
            
            # Go back to the previous page only after confirming section scraping is complete
            # self.driver.back()
            # WebDriverWait(self.driver, 5).until(
            #     EC.presence_of_element_located((By.ID, "navigation-index-see-all-licenses-and-certifications"))
            # )
            # self._random_delay(1, 2)
            
        except Exception as e:
            logging.warning(f"Failed to extract licenses: {str(e)}")
        print("returning licenses list", licenses_list)
        return licenses_list

    def save_to_file(self, data, filename):
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            logging.info(f"Data saved to {filename}")
        except Exception as e:
            logging.error(f"Failed to save data: {str(e)}")

    def close(self):
        print("in closing")
        try:
            self.driver.quit()
        except Exception as e:
            print("Error while quitting driver:", e)

        if self.driver:
            self.driver.quit()

def main():
    USERNAME = "foryouprem123@gmail.com"
    PASSWORD = "Mobis@7481"
    
    profiles = [
        "https://www.linkedin.com/in/julurisaichandu",
        "https://www.linkedin.com/in/saidheerajmalkar"
    ]
    
    scraper = LinkedInScraper()
    
    try:
        scraper.start_browser()
        scraper.login_to_linkedin(USERNAME, PASSWORD)
        
        all_profiles_data = []
        
        for profile_url in profiles:
            time.sleep(random.uniform(3, 6))
            profile_data = scraper.scrape_profile(profile_url)
            if profile_data:
                all_profiles_data.append(profile_data)
                scraper.save_to_file(all_profiles_data, 'linkedin_profiles.json')
            
    except Exception as e:
        logging.error(f"Scraping failed: {str(e)}")
    finally:
        scraper.close()

main()