from ClockInService import ClockInService
from ClockInService import Browser
from Share.ConfigTool import ConfigTool

class Main:
    def __init__(self):
        self.__clockInService = ClockInService()
        self.__Config = ConfigTool().get_config()
        self.__URL =self.__Config["104Web"]["URL"]
        self.__Username = self.__Config["104Web"]["Username"]
        self.__Password = self.__Config["104Web"]["Password"]


    def run(self):
        self.__clockInService.SetWebdriver(Browser.Chrome)
        self.__clockInService.Login(self.__URL,self.__Username,self.__Password)

if __name__ == '__main__':
    main = Main()
    main.run()

