import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains  


driver = webdriver.Chrome()

# Open the login page
driver.get("http://localhost:5000/login")  
time.sleep(1)  # Shorter pause for faster observation

# Wait for the login form to load and input credentials
WebDriverWait(driver, 20).until(
    EC.presence_of_element_located((By.NAME, "username_or_email"))
)

# Input the username or email
username_or_email = driver.find_element(By.NAME, "username_or_email")
username_or_email.send_keys("user_test")  
time.sleep(1)  

# Input the password
password = driver.find_element(By.NAME, "password")
password.send_keys("test1234")  
time.sleep(1)  

# Click the login button
submit_button = driver.find_element(By.XPATH, "//input[@type='submit']")
submit_button.click()
time.sleep(1)  

# Wait for the tree page to load 
WebDriverWait(driver, 5).until(
    EC.url_contains("/tree/Dehdashti")
)
print("Logged in and on the Dehdashti tree page:", driver.current_url)
time.sleep(1) 

# Navigate to the Home page from the navbar
home_link = WebDriverWait(driver, 20).until(
    EC.element_to_be_clickable((By.LINK_TEXT, "Home"))
)
home_link.click()
time.sleep(1)  

# Wait for the Home page to load
WebDriverWait(driver, 5).until(
    EC.url_contains("/")
)
print("On the Home page:", driver.current_url)
time.sleep(1)  

# Perform tests on the Home page

# Verify the presence of the "Get Started" button and click it
get_started_button = WebDriverWait(driver, 5).until(
    EC.element_to_be_clickable((By.ID, "started"))
)
time.sleep(1)  
get_started_button.click()
time.sleep(1)  

# Wait for the login page to reload as "Get Started" redirects to login if not logged in
WebDriverWait(driver, 5).until(
    EC.url_contains("/login")
)
print("Redirected back to the login page from Get Started:", driver.current_url)
time.sleep(1)  

# Go back to the Home page
driver.back()
time.sleep(1)  

# Verify the presence of the "Learn More" button and click it
learn_more_button = WebDriverWait(driver, 5).until(
    EC.element_to_be_clickable((By.ID, "learnMore"))
)
time.sleep(1)  
learn_more_button.click()
time.sleep(1)  

# Scroll to the "User Manual" button to bring it into view
user_manual_link = WebDriverWait(driver, 5).until(
    EC.element_to_be_clickable((By.ID, "usermanual"))
)
driver.execute_script("arguments[0].scrollIntoView(true);", user_manual_link)
time.sleep(1)  

user_manual_link.click()
time.sleep(1)  

# Check if the correct user manual PDF is opened in a new tab
driver.switch_to.window(driver.window_handles[-1])  # Switch to the new tab
WebDriverWait(driver, 20).until(
    EC.url_contains("/pdf/usermanual.pdf")
)
print("User manual PDF opened in a new tab:", driver.current_url)
time.sleep(1) 

# Close the PDF tab and switch back to the main window
driver.close()
driver.switch_to.window(driver.window_handles[0])


# Wait on the Home page for a few seconds to ensure everything is displayed correctly
time.sleep(2)  

# Close the browser after the test
driver.quit()
