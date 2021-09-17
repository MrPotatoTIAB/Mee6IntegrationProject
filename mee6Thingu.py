# =================================================
# =           Exceptions and Handlers             =
# =================================================
from time import time
from datetime import timedelta

disabledModules = []

class TooManyRequestsException(Exception):
    def __init__(self, retryAfter):
        print("Too many requests sent, please try again in {}.".format(timedelta(seconds=retryAfter)))
        write_config('u', {CFG_RETRY_AFTER: time() + retryAfter})

class LinkNotGenerated(Exception):
    def __init__(self):
        print("Link hasn't generated yet tried to connect to the api.")

try:


    # =================================================
    # =              Initialization                   =
    # =================================================

    # Import modules
    try:
        import requests
    except ModuleNotFoundError:
        print("The \"requests\" module has not found, this program requires it to run. Press enter to exit...")
        input()
        exit()
    import json
    from os.path import isfile
    from os import mkdir
    # import winsound
    from math import floor
    try:
        import keyboard as kb
    except ModuleNotFoundError as moduleError:
        print(f"Module {moduleError.name} not found, disabling modules relating to it.")
        disabledModules.append(moduleError.name)

    # Initialize variables
    xpLeft = 0
    timeLeft = 0
    serverID = 0
    interval = 60
    page_limit = 10
    prevInp = ""
    link = ""
    fullUsername = ""
    exitKey = "shift+esc"
    soundFile = "Sounds/pling.ogg"
    configFileLocation = "configs/mee6LevelUtilitiesConfig.json"
    configFolderLocation = "configs"
    config = {}
    configTemplate = {
        "savedServers": {},
        "savedUsernames": {},
        "lastlyUsedServer": "",
        "lastlyUsedUsername": "",
        "Retry-After": -1,
        "isTemp": False,
        "tempServerID": -1
    }
    CFG_SAVED_SERVERS = "savedServers"
    CFG_SAVED_USERS = "savedUsernames"
    CFG_LAST_SERVER = "lastlyUsedServer"
    CFG_LAST_USER = "lastlyUsedUsername"
    CFG_RETRY_AFTER = "Retry-After"
    CFG_IS_TEMP = "isTemp"
    CFG_TEMP_SERVER = "tempServerID"





    # =================================================
    # =                 Functions                     =
    # =================================================

    # Request data function
    def get_data(_current_page=0, _options=""):
        if link == "":
            raise LinkNotGenerated
        print(f"Connecting to Mee6 database on page {_current_page}...")
        r = requests.get(link + "?page={pg}".format(pg=_current_page))

        if r.ok:
            print("Connected the database!")
            r.close()
            if 's' in _options:
                return r.json()["guild"]["name"]
            return r.json()
        else:
            if r.status_code == 401:
                print("This server's leaderboard is private.")
            elif r.status_code == 404:
                print("Server could not be found.")
            elif r.status_code == 429:
                raise TooManyRequestsException(int(r.headers["Retry-After"]))
            elif r.status_code == 500:
                print("An error occurred on the server side.")
            else:
                print("An unexpected error occurred: {}".format(r.status_code))
            r.close()
            return {"error": r.status_code}


    def get_input(_options='su'):
        global link

        _result = []
        if 's' in _options:
            # Getting server ID from user
            _iterated = False

            while not _iterated or 'f' in _options:
                _serverID = input("Enter the ID of the server you want to check.\n>> ")
                if _serverID.isnumeric():
                    _result.append(_serverID)
                    break
                else:
                    print("Invalid ID.\n\n")
                _iterated = True
        if 'u' in _options:
            # Getting username from user
            while True:
                _fullUsername = input("Enter your username:\n>> ")
                if _fullUsername.count("#") > 0 and len(_fullUsername) <= 32:
                    break
                else:
                    print("That's not a valid username.")
            _result.append(_fullUsername)
        if len(_result) > 1:
            return _result
        elif len(_result) == 1:
            return _result[0]
        else:
            return


    def write_config(_options, *args):
        global config
        if 'i' == _options:
            try:
                mkdir(configFolderLocation)
            except FileExistsError:
                pass
            with open(configFileLocation, 'w') as _configFile:
                json.dump(configTemplate, _configFile, indent=2)
            return
        elif 'u' == _options:
            with open(configFileLocation, 'w') as _configFile:
                for arg in args:
                    config.update(arg)
                json.dump(config, _configFile, indent=2)

        else:
            raise TypeError("There's no such a option as: " + _options)


    # Read data from config file
    def read_config():
        try:
            if isfile(configFileLocation):
                with open(configFileLocation, "r") as _configFile:
                    _config = json.load(_configFile)
                return _config
            else:
                print("No config files found, creating new one.")
                write_config('i')
                return configTemplate
        except Exception as err:
            print("An error occurred while reading the config file.\n"
                  "Please report the error to the developer.\nError code: {}".format(err))
            exit()


    # noinspection PyTypeChecker,PyUnresolvedReferences
    def search(_fullUsername=fullUsername):
        print("Searching through the database...")
        _user = None
        _page = 0
        _index = 0
        _isLastPage = False
        _username, _userID = _fullUsername.split('#')
        while _user is None and _page <= page_limit:
            _data = get_data(_page)
            if "error" in _data:
                print("Error while searching user.")
                break
            for _currentUser in _data["players"]:
                if _currentUser["username"] == _username and _currentUser["discriminator"] == _userID:
                    print("Found user {usr} in {sv}!".format(usr=_username, sv=_data["guild"]["name"]))
                    return _page, _index
                _index += 1
            if _user is None:
                if len(_data["players"]) < 99:
                    print("Reached the end of the leaderboard.")
                    break
                _index = 0
                _page += 1
                requests.get(link)
        print("User not found.")
        return -1, -1


    # Initialization function
    def initialize():
        print("Starting initialization...")

        _linkGenerated = False
        global config
        global link

        # breakpoint()
        config = read_config()

        if config[CFG_RETRY_AFTER] > time():
            raise TooManyRequestsException(config[CFG_RETRY_AFTER] - time())

        if config[CFG_IS_TEMP]:
            write_config('u', {CFG_LAST_USER: "", CFG_LAST_SERVER: "", CFG_IS_TEMP: False})

        if config[CFG_TEMP_SERVER] != -1:
            write_config('u', {CFG_TEMP_SERVER: -1})

        if config[CFG_LAST_SERVER] != "":
            print("Found server ID from config!")
        else:
            print("Couldn't found a server ID, requesting one...")
            _linkGenerated = select('s')

        _linkGenerated or generateLink(config[CFG_SAVED_SERVERS][config[CFG_LAST_SERVER]])

        if config[CFG_LAST_USER] != "":
            print("Found username in config!")
        else:
            print("Couldn't find an username, requesting one...")
            select("u")
        # if fullUsername in config[CFG_SAVED_USERS] and len(config[CFG_SAVED_USERS][fullUsername]) >= config[CFG_LAST_SERVER]:
        if config[CFG_LAST_USER] != "" and not config[CFG_IS_TEMP] and config[CFG_LAST_SERVER] in config[CFG_SAVED_USERS][config[CFG_LAST_USER]]:
            # noinspection PyTypeChecker
            _page, _index = config[CFG_SAVED_USERS][config[CFG_LAST_USER]][config[CFG_LAST_SERVER]]
        else:
            _page, _index = search(config[CFG_LAST_USER])
        print("Initialization completed!")
        return _page, _index

        # if len(sys.argv) == 1:  # Checks if it has not run with parameters
        # RUNNING THE PROGRAM WITH PARAMETERS ARE UNUSED, USE CONFIG FILE INSTEAD

        #     print("Your user name is {usr} and your id is {id}.".format(usr=username, id=id))
        # elif len(sys.argv) == 3:  # Check if it has run with parameters
        #     _serverID = sys.argv[1]
        #     if not _serverID.isnumeric():
        #         print("Invalid ID.\n\n")
        #         exit()
        #     fullUsername = sys.argv[2]
        #     if fullUsername.count("#") > 0 and len(fullUsername) <= 32:
        #         username, _userID = fullUsername.rsplit("#")
        #     else:
        #         print("That's not a valid username.")
        #         exit()
        # else:
        #     print("Error.")
        #     exit()

        # Searching in the data base


    # Update function
    # noinspection PyUnresolvedReferences
    def update(_page, _index):
        global xpLeft

        _data = get_data(_page)
        if "error" in _data:
            print("An error occurred while updating.")
            return

        _user = _data["players"][_index]
        _username = _user["username"]
        _rank = _page * 100 + _index + 1
        _xpUntilLevelUp = _user["detailed_xp"][1]
        _currentLevelXp = _user["detailed_xp"][0]
        _currentLevel = _user["level"]
        _serverName = _data["guild"]["name"]
        xpLeft = _xpUntilLevelUp - _currentLevelXp

        print("{usr} from {sv}\n\nYou're currently level {lvl} and #{rnk}. \
        \nYou need {xp} exp more to advance to level {nlvl}.\
        \nEstimated required messages: {amsg}\
        \nWorst case: {wmsg}\
        \nBest case: {bmsg}".format(usr=_username,
                                    sv=_serverName,
                                    xp=xpLeft,
                                    lvl=_currentLevel,
                                    nlvl=_currentLevel + 1,
                                    rnk=_rank,
                                    amsg=floor(xpLeft / 20) + 1,
                                    wmsg=floor(xpLeft / 15) + 1,
                                    bmsg=floor(xpLeft / 25) + 1))


    # exp calculation formulas
    def nextLevelFormula(level):  # 5n²+40n+55 ty a lot for mumbo's dc server community <3
        return (5 * pow(level, 2)) + (40 * level) + 55


    def totalReqExpFormula(level):  # (n^3/3+n^2/2+n/6)*5+(n^2/2+n/2)*40+n*55 thanks a lot again <3
        return int((10 * pow(level, 3) + 135 * pow(level, 2) + (455 * level)) / 6)


    # grind function
    # noinspection PyUnresolvedReferences
    def grind(_page, _index, _targetLevel):

        _data = get_data(_page)
        if "error" in _data:
            print("An error occurred while updating.")
            return
        _user = _data["players"][_index]
        _totalXp = _user["xp"]
        _targetXp = totalReqExpFormula(_targetLevel)
        _requiredXp = _targetXp - _totalXp
        _progressPercent = (_totalXp / _targetXp) * 100
        if _requiredXp > 0:
            print("You need {xp} more exp to reach level {lvl}.\
            \nProgress: %{percent}\
            \nEstimated required messages: {amsg}\
            \nWorst case: {wmsg}\
            \nBest case: {bmsg}".format(xp=_requiredXp,
                                        lvl=_targetLevel,
                                        percent=_progressPercent,
                                        amsg=floor(_requiredXp / 20),
                                        wmsg=floor(_requiredXp / 15),
                                        bmsg=floor(_requiredXp / 25)))
        else:
            print("You have already surpassed level {lvl} by {xp} exp.\
            \nProgress: %{percent}".format(xp=-_requiredXp,
                                           lvl=_targetLevel,
                                           percent=_progressPercent))


    # for testing purposes
    # noinspection PyUnresolvedReferences
    def test():
        _data = get_data(0)
        if "error" in _data:
            print("Error.")
            return
        _user = _data["players"][0]
        if totalReqExpFormula(_user["level"]) == _user["xp"] - _user["detailed_xp"][0]:
            print("success!")
        else:
            print("fail. :(\nexpected {}\ngot      {}".format(_user["xp"] - _user["detailed_xp"][0],
                                                              totalReqExpFormula(_user["level"])))


    # for testing purposes, DO NOT USE FOR REASONS OTHER THAN TESTING
    def spam():
        while True:
            get_data()


    # Show rank function
    def show_rank(_serverName=None, _xpLeft=None, _level=None, _rank=None):
        pass  # TODO add a show rank function instead showing it in update function


    # save to config function
    def save():
        if config[CFG_IS_TEMP]:
            _username = config[CFG_LAST_USER]
            _server = config[CFG_LAST_SERVER]
            _serverID = config[CFG_TEMP_SERVER]
            _index = index
            _page = page

            _tempDict = config[CFG_SAVED_USERS].copy()
            _tempDict.update({_username: {_server: [_page, _index]}})
            write_config('u', {CFG_SAVED_USERS: _tempDict, CFG_IS_TEMP: False})

            if _server not in config[CFG_SAVED_USERS]:
                _tempDict = config[CFG_SAVED_SERVERS].copy()
                _tempDict.update({_server: _serverID})
                write_config('u', {CFG_SAVED_SERVERS: _tempDict})


    # select from config function
    # noinspection PyUnboundLocalVariable
    def select(option):
        global page
        global index
        _linkGenerated = False

        if "s" in option:
            _selectionList = []
            for i, _server in enumerate(config[CFG_SAVED_SERVERS]):
                print(f"{i}: {_server}")
                _selectionList.append(_server)
            print("\nIf you want to enter a new name, type 'new'.")
            'f' in option or print("Entering an invalid option will quit.")
            _success = False
            _iterated = False
            _isNew = False
            while 'f' in option or not _iterated:
                _selection = input(">> ")
                if _selection == "":
                    pass
                elif _selection == "new":
                    _isNew = True
                    _result = get_input('s')
                    if _result is None:
                        continue
                    generateLink(_result)
                    _linkGenerated = True
                    _selection = get_data(_options='s')
                    if "error" in _selection:
                        _linkGenerated = False
                        _isNew = False
                    else:
                        write_config('u', {CFG_IS_TEMP: True})
                        _success = True
                        break
                elif not _selection.isnumeric():
                    print("You need to enter a number.")
                elif int(_selection) >= len(config[CFG_SAVED_SERVERS]):
                    print("This option is out of index.")
                else:
                    _result = config[CFG_SAVED_SERVERS][_selectionList[int(_selection)]]
                    _success = True
                    break
                _iterated = True
            if _success:
                if not _isNew:
                    write_config('u', {CFG_LAST_SERVER: _selectionList[int(_selection)]})
                else:
                    write_config('u', {CFG_LAST_SERVER: _selection, CFG_TEMP_SERVER: _result})
                print("You've selected {}.".format(config[CFG_LAST_SERVER]))
                generateLink(_result)
                if config[CFG_LAST_USER] == "":
                    print("No users found to search, requesting one...")
                    select('uf')
                if config[CFG_IS_TEMP] or config[CFG_LAST_SERVER] not in config[CFG_SAVED_USERS][config[CFG_LAST_USER]]:
                    print((config[CFG_IS_TEMP] and "The user wasn't saved, " or "The user can't be found in the config, ") + "searching on the Mee6 database...")
                    # page, index = search(config[CFG_LAST_USER])
                    config[CFG_IS_TEMP] or write_config('u', {CFG_IS_TEMP: True})
                else:
                    page, index = config[CFG_SAVED_USERS][config[CFG_LAST_USER]][config[CFG_LAST_SERVER]]
                    print("Server has been switched successfully")
            else:
                print("Exiting...")



        if "u" in option:
            print("Select which user you want to check:")
            _selectionList = []
            i = 0
            for _user in config[CFG_SAVED_USERS]:
                for _servers in config[CFG_SAVED_USERS][_user]:
                    if config[CFG_LAST_SERVER] in _servers:
                        _selectionList.append(_user)
                        print(f"{i}: {_user}")
                        i += 1
            print("\nIf you want to enter a new name, type 'new'.")
            'f' in option or print("Entering an invalid option will quit.")
            _success = False
            _iterated = False
            while 'f' in option or not _iterated:
                _selection = input(">> ")
                if _selection == "":
                    pass
                elif _selection == "new":
                    _result = get_input('u')
                    write_config('u', {CFG_LAST_USER: _result, CFG_IS_TEMP: True})
                    _success = True
                    break
                elif not _selection.isnumeric():
                    print("You need to enter a number.")
                elif int(_selection) >= len(_selectionList):
                    print("This option is out of index.")
                else:
                    _result = _selectionList[int(_selection)]
                    _success = True
                    break
                _iterated = True
            if _success:
                # noinspection PyUnboundLocalVariable
                if _result in config[CFG_SAVED_USERS]:
                    write_config('u', {CFG_LAST_USER: _result})
                    page, index = config[CFG_SAVED_USERS][config[CFG_LAST_USER]][config[CFG_LAST_SERVER]]
                # else:
                #     print("No such data found in the config, searching user...")
                #     page, index = search(_result)

                print("You've selected {}.".format(config[CFG_LAST_USER]))
            else:
                print("Exiting...")
        return _linkGenerated



    def generateLink(serverID):
        global link
        link = "https://mee6.xyz/api/plugins/levels/leaderboard/" + str(serverID)



    def verify(option, arg):
        if option == 'a':
            pass



    def help_command():
        print('"update [-n | -a | -l]": Updates from database and shows your rank.\n'
              'Options: "-n": Shows the level of the person next in the leaderboard.\n'
              '         "-a": Automatically updates every minute.\n'
              '         "-l (integer)": Shows required exp and percentage for the level you\'ve specified.\n\n'
              '"exit [option]": Exits from program.\n'
              'Aliases: "quit"\n'
              'Options: "-w": You\'ll be prompted to enter new user and server ID on next start.\n\n'
              '"select (-u | -s)": Allows you to select a saved or new user or server.\n'
              'Options: "-u": Selects a user.\n'
              '         "-s": Selects a server.\n\n'
              '"help": Pretty self explanatory, isn\'t it?\n\n'
              '"save": Allows you to save the current user and server.\n\n'
              'Pro tip: Sending a blank line runs the previous command you\'ve used.')
        pass  # TODO make help section


    # =================================================
    # =                Shell Loop                     =
    # =================================================
    if __name__ == "__main__":
        prevTime = time()
        page, index = initialize()
        while True:
            inp = input(">> ").split(" ")
            if inp[0] == "" and prevInp is not None:
                inp = prevInp
            prevInp = inp
            if inp[0] == "update":
                if len(inp) > 1:
                    if inp[1] == "-n":
                        if index < 1:
                            if page < 1:
                                print("You're already number one.")
                            else:
                                update(page - 1, 99)
                        else:
                            update(page, index - 1)
                    elif inp[1] == "-a":
                        if "keyboard" not in disabledModules:
                            while True:
                                if timeLeft <= 0:
                                    timeLeft = interval
                                    update(page, index)
                                    # if xpLeft <= 100:  # TODO Alarm is currently under-construct
                                    #     for i in range(5):
                                    #         winsound.PlaySound(soundFile,
                                    #                            winsound.SND_FILENAME ^ winsound.SND_ASYNC ^ winsound.SND_NODEFAULT)
                                else:
                                    tempTime = time()  # delta time :>
                                    timeLeft -= tempTime - prevTime
                                    prevTime = tempTime
                                if kb.is_pressed(exitKey):
                                    break
                        else:
                            print("The module \"keyboard\" required to use this feature.")
                    elif inp[1] == "-l":
                        if len(inp) > 2 and inp[2].isdecimal():
                            grind(page, index - 1, int(inp[2]))
                        else:
                            print("Invalid argument: " + (len(inp) > 2 and f"{inp[2]}" or "Missing argument."))
                    else:
                        print(f"Invalid argument: \"{inp[1]}\"")
                else:
                    update(page, index)
            elif inp[0] in ["exit", "quit"]:
                if "-w" in inp:
                    write_config('u', {CFG_IS_TEMP: True})
                print("Exiting...")
                exit()
            elif inp[0] == "test":
                test()
            elif inp[0] == "select":
                if len(inp) < 2:
                    print("Not enough parameters.")
                elif inp[1] == "-u":
                    select("u")
                elif inp[1] == "-s":
                    select("s")
                else:
                    print(f"Invalid argument: {inp[1]}")
            elif inp[0] == "spam":
                print("THIS ONLY FOR DEBUG PURPOSES, ONLY USE WHEN DEVELOPER SAID SO."
                      "\nDo you want to proceed? y/n")
                secInp = input(">> ")
                if secInp == 'y':
                    spam()
                elif secInp == 'n':
                    print("Aborting...")
                else:
                    print("Unknown option, assuming as no...")
            elif inp[0] == "help":
                help_command()
            elif inp[0] == "save":
                save()
            else:
                print("Unknown command. Type \"help\" for commands.")


# Exiting the program
except TooManyRequestsException:
    pass

except Exception as error:
    print("An unexpected error occurred, the error is:\n"
          f"\"{error}\"\n"
          "Please report this bug to developer...")
    raise error
finally:  # For debugging purposes
    if __name__ == "__main__":
        from time import sleep
        for i in range(3):
            print('.', end="")
            sleep(1)
        print()
#     breakpoint()
#     pass


# addentium:
#
# TODO: add color and fancy stuff.
# tip: import colorama
# thanks a lot to Quon for showing me such a lib exists.
