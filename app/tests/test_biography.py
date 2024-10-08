import unittest
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

class BiographyPageTest(unittest.TestCase):
    def setUp(self):
        self.driver = webdriver.Chrome()
        self.driver.get("http://127.0.0.1:5000/biography")
        self.wait = WebDriverWait(self.driver, 10) 
        

    def tearDown(self):
        self.driver.quit()
    
    #Test submitting a comment on the biography page
    def test_Submit_Comment(self):
            self.driver.get("http://127.0.0.1:5000/login")
            username_input = self.driver.find_element(By.NAME, "username_or_email")
            password_input = self.driver.find_element(By.NAME, "password")
            submit_button = self.driver.find_element(By.TAG_NAME, "button")
            username_input.send_keys("user_test")
            password_input.send_keys("test1234")
            submit_button.click()

            self.driver.get("http://127.0.0.1:5000/biography/%DA%A9%D8%B1%D8%A8%D9%84%D8%A7%DB%8C%DB%8C%20%D8%BA%D9%84%D8%A7%D9%85%20%D8%AD%D8%B3%DB%8C%D9%86")
            comment_input = self.driver.find_element(By.NAME, "comment")
            submit_button = self.driver.find_element(By.TAG_NAME, "button")
            comment_input.send_keys("This is a test comment.")
            submit_button.click()
            new_comment = self.driver.find_element(By.XPATH, "//p[contains(text(),'This is a test comment.')]")
            self.assertTrue(new_comment.is_displayed())
            
        
    #Test that non admin user cannot access this edit biography page 
    def test_non_admin_cannot_edit_biography(self):
            self.driver.get("http://127.0.0.1:5000/login")
            username_input = self.driver.find_element(By.NAME, "username_or_email")
            password_input = self.driver.find_element(By.NAME, "password")
            submit_button = self.driver.find_element(By.TAG_NAME,"button")
            username_input.send_keys("user_test")
            password_input.send_keys("test1234")
            submit_button.click()

            self.driver.get("http://127.0.0.1:5000/biography/edit")
            response = self.driver.find_element(By.TAG_NAME,"body").text
            self.assertNotIn('Edit Biography', response)
            self.assertIn('You do not have permission to edit this biography', response)

       
    

if __name__ == "__main__":
    unittest.main()