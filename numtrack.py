#!/usr/bin/env python3
# NumTrackX - Advanced Phone Number OSINT Tool

import phonenumbers
from phonenumbers import geocoder, carrier
import requests, sqlite3, time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from fake_useragent import UserAgent

DB = 'numtrack.db'

def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS numlogs (
        number TEXT, country TEXT, carrier TEXT, dork TEXT, whatsapp TEXT, timestamp TEXT
    )''')
    conn.commit()
    conn.close()

def validate_number(number):
    parsed = phonenumbers.parse(number)
    if not phonenumbers.is_valid_number(parsed):
        return None
    country = geocoder.description_for_number(parsed, 'en')
    sim = carrier.name_for_number(parsed, 'en')
    return country, sim

def google_dork(number):
    query = f'"{number}"'
    headers = {'User-Agent': UserAgent().random}
    url = f"https://www.google.com/search?q={query}"
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')
    results = soup.find_all('div', class_='BNeawe vvjwJb AP7Wnd')
    return results[0].text if results else 'No public info'

def whatsapp_check(number):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    try:
        driver.get(f'https://wa.me/{number.replace("+", "")}')
        time.sleep(5)
        if "WhatsApp" in driver.page_source and "Continue to Chat" in driver.page_source:
            return "Active"
        else:
            return "Inactive"
    except:
        return "Error"
    finally:
        driver.quit()

def save_result(number, country, sim, dork, wa_status):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("INSERT INTO numlogs VALUES (?, ?, ?, ?, ?, ?)", (
        number, country, sim, dork, wa_status, time.ctime()
    ))
    conn.commit()
    conn.close()

def run_lookup(number):
    print(f"[+] Checking: {number}")
    val = validate_number(number)
    if not val:
        print("[-] Invalid Number Format!")
        return

    country, sim = val
    print(f"    Country: {country}")
    print(f"    Carrier: {sim}")

    dork = google_dork(number)
    print(f"    Dork Result: {dork}")

    wa_status = whatsapp_check(number)
    print(f"    WhatsApp: {wa_status}")

    save_result(number, country, sim, dork, wa_status)
    print("[+] Result saved to DB.")

if __name__ == "__main__":
    init_db()
    num = input("Enter phone number with +countrycode: ")
    run_lookup(num)
