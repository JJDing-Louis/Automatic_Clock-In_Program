from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from enum import Enum

class Browser(str,Enum):
    Chrome = "chrome"
    Firefox = "firefox"
    Edge = "edge"

class ClockInService:
    def __init__(self):
        self.__URL = ""
        self.__UserName = ""
        self.__Password = ""
        self.__options = None
        self.__driver = None
        self.__timedelay=None

    def SetWebdriver(self, BrowserName: Browser):
        if not isinstance(BrowserName, Browser):
            raise ValueError(f"BrowserName 必須是 Browser Enum 的成員，例如: {list(Browser)}")
        match BrowserName.lower():
            case Browser.Chrome:
                self.__options = webdriver.ChromeOptions()
                self.__options.add_experimental_option("detach", True)
                self.__driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=self.__options)

            case Browser.Firefox:
                self.__options = webdriver.FirefoxOptions()
                self.__driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()), options=self.__options)

            case Browser.Edge:
                self.__options = webdriver.EdgeOptions()
                self.__driver = webdriver.Edge(service=EdgeService(EdgeChromiumDriverManager().install()), options=self.__options)

            case _:
                raise ValueError(f"不支援的瀏覽器: {BrowserName}")

        return self.__driver

    def Login(self,URL,UserName,Password):
        self.__URL = URL
        self.__UserName = UserName
        self.__Password = Password
        # 定位帳號輸入框並輸入帳號
        self.__driver.get(self.__URL)
        wait = WebDriverWait(self.__driver, 10)
        self.__LoginButton = wait.until(EC.element_to_be_clickable(self.__driver.find_element(By.CSS_SELECTOR, '[data-qa-id="loginButton"]')))
        self.__UserNameTextBox = self.__driver.find_element(By.CSS_SELECTOR, '[data-qa-id="loginUserName"]')
        self.__UserNameTextBox.send_keys(self.__UserName)
        # 定位密碼輸入框並輸入密碼
        self.__PasswordTextBox = self.__driver.find_element(By.CSS_SELECTOR, '[data-qa-id="loginPassword"]')
        self.__PasswordTextBox.send_keys(self.__Password)
        # 按下登入
        self.__LoginButton.click()
