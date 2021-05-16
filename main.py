from datetime import datetime, date, timedelta
import yaml
from bs4 import BeautifulSoup
from time import sleep
from selenium import webdriver
import argparse
from os import system

SPORTS_CODES = {
    "fitness": 122920,
}
LOCATIONS_CODES = {
    "polyterasse": 45594,
    "honggerberg": 45598,
    "irchel": 45577,
    "fluntern": 45575,
    "winterthur": 45610,
    "wadensvil": 45613
}

BASE_URL = "https://schalter.asvz.ch/"


def setupSelenium():
    user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'

    options = webdriver.ChromeOptions()

    # Ignore TLS certificate errors to prevent errors. No special requirement for security here
    options.add_argument('--ignore-certificate-errors')

    # Sets up the browser to be in incognito mode
    options.add_argument('--incognito')

    # Forces the driver to be in English for compatability matters
    options.add_experimental_option(
        'prefs', {'intl.accept_languages': 'en,en_US'})
    options.add_argument(f'user-agent={user_agent}')

    driver = webdriver.Chrome(
        '/usr/lib/chromium-browser/chromedriver', options=options)
    return driver


def getCredentials():
    with open("/home/pi/Dev/Github/ASVZRegisterBot/creds.yaml") as creds_file:
        creds = yaml.load(creds_file, Loader=yaml.FullLoader)

    username = creds["username"]
    password = creds["password"]

    return username, password


def log(message: str):
    now = datetime.now()
    date_string = now.strftime("%d.%m.%Y %H:%M:%S")
    system(
        f'echo "[{date_string}] {message}" >> /home/pi/Dev/Github/ASVZRegisterBot/myjob.log')
    print(message)


def switchLogin(driver):
    username, password = getCredentials()

    sleep(1)
    switch_login = "btn-warning"
    driver.find_element_by_class_name(switch_login).click()
    sleep(1)

    textbox = "idd_textbox"
    driver.find_element_by_class_name(textbox).click()

    sleep(1)
    x_path = "//div[@savedvalue=\"https://aai-logon.ethz.ch/idp/shibboleth\"]"
    driver.find_element_by_xpath(x_path).click()
    sleep(1)

    username_xpath = "//input[@name=\"j_username\"]"
    username_field = driver.find_element_by_xpath(username_xpath)
    username_field.send_keys(username)

    password_xpath = "//input[@name=\"j_password\"]"
    password_field = driver.find_element_by_xpath(password_xpath)
    password_field.send_keys(password)

    elem = driver.find_element_by_xpath("//button[@type=\"submit\"]")

    elem.click()
    sleep(2)


def getTomorrowsDate():
    tomorrow = date.today() + timedelta(days=1)
    d = tomorrow.strftime("%Y-%m-%d")
    return d


def getLecturesFiltered(driver, date, location, sport):
    s = SPORTS_CODES[sport]
    l = LOCATIONS_CODES[location]
    url = f"https://asvz.ch/426-sportfahrplan?f[0]=sport:{s}&f[1]=facility:{l}&date={date}"
    try:
        driver.get(url)
        sleep(2)
    except:
        exit("Could not access URL")


def getLecturePage(driver):
    lecture_x_path = "//*[@id=\"block-asvz-next-content\"]/div/div[1]/div[2]/div[4]/div[1]/div/ul/li[1]/a"

    freie_platze_x_path = "//*[@id=\"block-asvz-next-content\"]/div/div[1]/div[2]/div[4]/div[1]/div/ul/li[1]/a/div[3]/div/div/div/div[2]"

    freie_platze = True
    try:
        sleep(2)
        driver.find_element_by_xpath(
            freie_platze_x_path).text[:5].lower() == "freie"
    except:
        freie_platze = False

    if not freie_platze:
        raise Exception(
            "You cannot register for now (either too early, too late or no more places.")
    else:
        lecture_url = driver.find_element_by_xpath(
            lecture_x_path).get_attribute("href")
        return lecture_url


def registerToLecture(driver, url):
    driver.get(url)
    sleep(1)
    driver.get(url)
    sleep(4)
    einschreiben_button = driver.find_element_by_xpath(
        "//*[@id=\"btnRegister\"]")

    try:
        if "einschreiben" in einschreiben_button.text.lower():
            einschreiben_button.click()
            log("You were successfully registered!")
        else:
            raise Exception("You are already registered")
    except:
        raise Exception("Oops... Couldn't find registration button")


def registerToASVZEvent(location, sport, hour):
    driver = setupSelenium()
    log("Driver setup")
    driver.get(BASE_URL)
    switchLogin(driver)
    log("Successfully logged in")
    tomorrow = getTomorrowsDate()
    lecture_date = tomorrow + "%20" + hour
    getLecturesFiltered(driver=driver, date=lecture_date,
                        location=location, sport=sport)

    try:
        lectureURL = getLecturePage(driver)
        registerToLecture(driver, url=lectureURL)
    except Exception as e:
        log(e)
    driver.quit()


def getArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--sport", "-s", help="The sport you want to register to", choices=list(SPORTS_CODES.keys()))
    parser.add_argument(
        "--hour", "-hr", help="The hour you want to book to the next day. Must be of the form \"HH:MM\"")
    parser.add_argument(
        "--location", "-l", help="The location in which the lecture takes place", choices=list(LOCATIONS_CODES.keys()))

    return parser.parse_args()


if __name__ == "__main__":
    log("Bot started")
    args = getArgs()
    log(f"Location: {args.location}")
    log(f"Hour: {args.hour}")
    log(f"Sport: {args.sport}\n")

    registerToASVZEvent(location=args.location,
                        hour=args.hour, sport=args.sport)
