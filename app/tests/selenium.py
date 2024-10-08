
import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
## TESTS DONE BY JOSH COOPER
class TreePageLoadingTest(unittest.TestCase):
    def setUp(self):
        #opening web driver in chrome
        self.driver = webdriver.Chrome()
    def tearDown(self):
        # Closing the browser
        self.driver.quit()
    def Tree_Loading_Test(self):
        # find the chart page
        self.driver.get("http://127.0.0.1:5000/tree")
        #get  bar chart by ID
        TreeGraph = self.driver.find_element(By.ID,"graph")
        # check if displayed 
        self.assertTrue(TreeGraph.is_displayed())

    def test_Form_Loads(self):
        # same as before but for the existing feedback
        self.driver.get("http://127.0.0.1:5000/modify_graph")
        
        Form = self.driver.find_element(By.CLASS_NAME,"Form")
        
        self.assertTrue(Form.is_displayed())

if __name__ == "__main__":
    unittest.main()
