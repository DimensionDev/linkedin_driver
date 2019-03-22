__site_url__ = 'https://www.linkedin.com'

import bs4
import metadrive

from metadrive._selenium import get_driver

def _login(
        username=None,
        password=None,
        profile='default',
        recreate_profile=False,
        headless=False,
        proxies='default',
        drive=None,
        refresh=False):
    '''
    Accepts: username/password.
    Returns: driver with logged-in state.

    TODO:
    Handle this in the future:

    1. LinkedIn asks to verify e-mail address if it sees too often log-ins.
    2. LinkedIn asks to enter phone number
    '''
    if drive is not None:
        driver = drive
    elif proxies is not None:
        driver = get_driver(profile=profile, recreate_profile=recreate_profile, proxies=proxies, headless=headless)
    else:
        driver = get_driver(profile=profile, recreate_profile=recreate_profile, headless=headless)

    driver.get(__site_url__)
    soup = bs4.BeautifulSoup(driver.page_source, 'html.parser')

    if soup.find('div', {'class': 'core-rail'}):
        driver.metaname = metadrive.utils.get_metaname('linkedin')
        return driver

    if not (username and password):
        credential = metadrive.utils.get_or_ask_credentials(
            namespace='linkedin',
            variables=['username', 'password'], ask_refresh=refresh)

        username = credential['username']
        password = credential['password']

    user_field = soup.find('input', {'class': 'login-email'})
    pass_field = soup.find('input', {'class': 'login-password'})

    if user_field and pass_field:

        driver.find_element_by_class_name('login-email').send_keys(username)
        driver.find_element_by_class_name('login-password').send_keys(password)
        driver.find_element_by_id('login-submit').click()
        soup = bs4.BeautifulSoup(driver.page_source, 'html.parser')

        if soup.find('div', {'id': 'error-for-password'}):
            raise Exception("Incorrect password. Try to relogin.")

        if soup.find('button', {'class': 'artdeco-dismiss'}):
            'Removing the notification about cookies.'
            driver.find_element_by_class_name('artdeco-dismiss').click()

    soup = bs4.BeautifulSoup(driver.page_source, 'html.parser')

    asks_something = soup.find('h2', {'class': 'headline'})
    if asks_something is not None:
        if asks_something.text == 'Add a phone number':
            raise Exception('LinkedIn asks for Phone Number, suggest using proxies, for example, just pass get_driver(proxies={"socksProxy": "127.0.0.1:9999"})...')

    if soup.find('li', {'id': 'profile-nav-item'}):
        return driver
    else:
        raise Exception("Something wrong, the site does not have profile (user-dropdown).")

def _harvest():
    from linkedin_driver.api import Post
    return Post._filter()
