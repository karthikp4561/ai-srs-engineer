import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

BASE_URL = "http://localhost:4200"
WAIT_TIME = 15

# Use unique emails each run so registration never collides with a previous test run
suffix = random.randint(1000, 9999)
OWNER_EMAIL = f"owner{suffix}@test.com"
OWNER_NAME = "OwnerUser"
OWNER_PASSWORD = "testpass123"

COLLAB_EMAIL = f"collab{suffix}@test.com"
COLLAB_NAME = "CollabUser"
COLLAB_PASSWORD = "testpass123"

PROJECT_TITLE = f"Selenium Test Project {suffix}"
PROJECT_DESC = "A test project created by an automated Selenium test to verify the collaboration module works end to end."


def new_driver():
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    driver.maximize_window()
    return driver


def register(driver, name, email, password):
    driver.get(f"{BASE_URL}/register")
    WebDriverWait(driver, WAIT_TIME).until(EC.presence_of_element_located((By.NAME, "name")))
    driver.find_element(By.NAME, "name").send_keys(name)
    driver.find_element(By.NAME, "email").send_keys(email)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    WebDriverWait(driver, WAIT_TIME).until(EC.url_contains("/login"))
    print(f"[OK] Registered {email}")


def login(driver, email, password):
    driver.get(f"{BASE_URL}/login")
    WebDriverWait(driver, WAIT_TIME).until(EC.presence_of_element_located((By.NAME, "email")))
    driver.find_element(By.NAME, "email").send_keys(email)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    WebDriverWait(driver, WAIT_TIME).until(EC.url_contains("/dashboard"))
    print(f"[OK] Logged in as {email}")


def create_project(driver, title, description):
    driver.get(f"{BASE_URL}/new-project")
    WebDriverWait(driver, WAIT_TIME).until(EC.presence_of_element_located((By.NAME, "title")))
    driver.find_element(By.NAME, "title").send_keys(title)
    driver.find_element(By.NAME, "description").send_keys(description)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    WebDriverWait(driver, WAIT_TIME).until(EC.url_contains("/dashboard"))
    print(f"[OK] Created project '{title}'")


def open_project_by_title(driver, title):
    driver.get(f"{BASE_URL}/dashboard")
    WebDriverWait(driver, WAIT_TIME).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".project-card")))
    cards = driver.find_elements(By.CSS_SELECTOR, ".project-card")
    for card in cards:
        if title in card.text:
            card.click()
            WebDriverWait(driver, WAIT_TIME).until(EC.url_contains("/projects/"))
            print(f"[OK] Opened project '{title}'")
            return
    raise Exception(f"Project '{title}' not found on dashboard")


def invite_collaborator(driver, email, role="editor"):
    email_input = WebDriverWait(driver, WAIT_TIME).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".invite-row input[type='email']"))
    )
    email_input.send_keys(email)

    role_select = driver.find_element(By.CSS_SELECTOR, ".invite-row select")
    role_select.send_keys(role)

    invite_button = driver.find_element(By.XPATH, "//div[contains(@class,'invite-row')]//button")
    invite_button.click()

    time.sleep(2)  # allow the invite request + list refresh to complete
    print(f"[OK] Invited {email} as {role}")


def verify_collaborator_listed(driver, email):
    WebDriverWait(driver, WAIT_TIME).until(
        lambda d: email in d.find_element(By.CSS_SELECTOR, ".collab-list").text
    )
    print(f"[OK] Verified {email} appears in collaborator list")


def verify_shared_project_visible(driver, title):
    driver.get(f"{BASE_URL}/dashboard")
    WebDriverWait(driver, WAIT_TIME).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    time.sleep(2)
    assert title in driver.page_source, f"Shared project '{title}' not visible on collaborator's dashboard"
    print(f"[OK] Verified '{title}' appears under Shared with You")


def run_test():
    owner_driver = new_driver()
    collab_driver = new_driver()

    try:
        # Set up both users
        register(owner_driver, OWNER_NAME, OWNER_EMAIL, OWNER_PASSWORD)
        register(collab_driver, COLLAB_NAME, COLLAB_EMAIL, COLLAB_PASSWORD)

        # Owner creates a project and invites the collaborator
        login(owner_driver, OWNER_EMAIL, OWNER_PASSWORD)
        create_project(owner_driver, PROJECT_TITLE, PROJECT_DESC)
        open_project_by_title(owner_driver, PROJECT_TITLE)
        invite_collaborator(owner_driver, COLLAB_EMAIL, role="editor")
        verify_collaborator_listed(owner_driver, COLLAB_EMAIL)

        # Collaborator logs in and checks the project is visible to them
        login(collab_driver, COLLAB_EMAIL, COLLAB_PASSWORD)
        verify_shared_project_visible(collab_driver, PROJECT_TITLE)

        print("\n✅ ALL COLLABORATION TESTS PASSED")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        owner_driver.save_screenshot("owner_failure.png")
        collab_driver.save_screenshot("collab_failure.png")
        raise

    finally:
        time.sleep(3)
        owner_driver.quit()
        collab_driver.quit()


if __name__ == "__main__":
    run_test()