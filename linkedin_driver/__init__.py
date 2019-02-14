__site_url__ = 'https://www.linkedin.com'

import sys
import re
import time
import bs4
import time
import urllib

from metadrive import utils
from metadrive._selenium import get_driver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait

import logging


def login(username=None, password=None, profile=None, recreate_profile=False, proxies=None):
    '''
    Accepts: username/password.
    Returns: driver with logged-in state.
    wd
    '''
    # TODO:
    # Handle this in the future:
    #
    # 1. LinkedIn asks to verify e-mail address if it sees too often log-ins.
    # 2. LinkedIn asks to enter phone number
    if proxies is not None:
        driver = get_driver(recreate_profile=recreate_profile, proxies=proxies)
    else:
        driver = get_driver(recreate_profile=recreate_profile)

    driver.get(__site_url__)
    soup = bs4.BeautifulSoup(driver.page_source, 'html.parser')

    if soup.find('div', {'class': 'core-rail'}):
        driver.metaname = utils.get_metaname('linkedin')
        return driver

    if not (username and password):
        credential = utils.get_or_ask_credentials(
            namespace='linkedin',
            variables=['username', 'password'], ask_refresh=True)

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


def open_contact(contact_url='https://www.linkedin.com/in/austinoboyle/'):
    '''needs to be called twice'''

    driver.get(urllib.parse.urljoin(contact_url, 'detail/contact-info/'))
    contact_soup = bs4.BeautifulSoup(driver.page_source, 'html.parser')

    career_card = contact_soup.find('section', {'class': 'pv-contact-info__contact-type ci-vanity-url'})
    if career_card is not None:
        profile_url = [search['href'] for search in career_card.find_all('a')]
    else:
        profile_url = None
        logging.warning('profle not found.')

    website = contact_soup.find('section', {'class': 'pv-contact-info__contact-type ci-websites'})
    if website is not None:
        web_url = [search['href'] for search in website.find_all('a')]
        web_type = [search.text.strip() for search in website.find_all('span')]
        websites = []
        for i in range(len(web_url)):
            websites.append({'type':web_type[i],'url':web_url[i]})
    else:
        websites = None

    twitter = contact_soup.find('section', {'class': 'pv-contact-info__contact-type ci-twitter'})
    if twitter is not None:
        twitter_url = twitter.find('a')['href']
    else:
        twitter_url = None


    contact = {"profile_url": profile_url, "websites": websites,'twitter':twitter_url}

    close = driver.find_element_by_class_name('artdeco-dismiss')
    ActionChains(driver).move_to_element(close).click().perform()

    #
    # close_card =  contact_soup.find('div', {'class': 'pv-uedit-photo-card'})
    # if close_card is not None:
    #     try:
    #     driver.find_element_by_class_name('pv-uedit-photo-card__dismiss').click()
    #     explain the reasons why op-out-of-photo
    #

    return contact


def scroll_to_bottom(contact_url='https://www.linkedin.com/in/austinoboyle/'):
    if contact_url is not None:
        driver.get(contact_url)
    #Scroll to the bottom of the page
    expandable_button_selectors = [
        'button[aria-expanded="false"].pv-skills-section__additional-skills',
        'button[aria-expanded="false"].pv-profile-section__see-more-inline',
        'button[aria-expanded="false"].pv-top-card-section__summary-toggle-button'
    ]
    current_height = 0
    while True:
        for name in expandable_button_selectors:
            try:
                driver.find_element_by_css_selector(name).click()
            except:
                pass
        # Scroll down to bottom
        new_height = driver.execute_script(
            "return Math.min({}, document.body.scrollHeight)".format(current_height + 280))
        if (new_height == current_height):
            break
        driver.execute_script(
            "window.scrollTo(0, Math.min({}, document.body.scrollHeight));".format(new_height))
        current_height = new_height
        # Wait to load page
        time.sleep(0.4)


def open_interest(contact_url='https://www.linkedin.com/in/austinoboyle/'):
    '''if it crashes, try it several times'''

    driver.get(urllib.parse.urljoin(contact_url, 'detail/interests'))
    #driver.get(urllib.parse.urljoin(contact_url, 'detail/interests/companies/'))

    interest_selector = [
        'a[data-control-name="following_companies"]',
        'a[data-control-name="following_groups"]',
        'a[data-control-name="following_schools"]']

    interests = []

    def extract_interest(soup):
        '''
        helper function to extract each interest
        '''
        box = []
        for item in soup.find_all('li',{'class' : 'entity-list-item'}):
            box.append({
                'img':item.find('img',{"src":True}),
                'name':item.find('span',{'class':'pv-entity__summary-title-text'}).text,
                'number of followers':item.find('p',{'class':'pv-entity__follower-count'}).text.split(" ")[0]
            })
        return box

    for name in interest_selector:
        try:
            driver.find_element_by_css_selector(name).click()
        except:
            pass
        try:
            list_wrapper =  driver.find_element_by_xpath('//div[@class="entity-list-wrapper ember-view"]//a')
            list_wrapper.send_keys(Keys.END)
            time.sleep(2)
        except:
            soup = bs4.BeautifulSoup(driver.page_source, 'html.parser')
            interests.append(extract_interest(soup))
            pass
        soup = bs4.BeautifulSoup(driver.page_source, 'html.parser')
        interests.append(extract_interest(soup))
    
    classification = ['companies','groups','schools']
    result = zip(classification,interests)
        
    close = driver.find_element_by_class_name('artdeco-dismiss')
    close.click()

    return list(result)


def text_or_default_accomp(element, selector, default=None):
    try:
        s = element.select_one(selector).get_text().strip().split('\n')
        if len(s) == 2:
            return s[1].strip()
        else:
            return s[0].strip()
    except Exception as e:
        return default


def open_accomplishments():

    soup0 = bs4.BeautifulSoup(driver.page_source,'html.parser')

    classification = []

    for cla in soup0.find_all('h3',{'class':'pv-accomplishments-block__title'}):
        classification.append(cla.text)

    accomp_expand = driver.find_elements_by_class_name('pv-accomplishments-block__expand')

    expand_box = soup0.find_all(class_ = 'pv-profile-section__see-more-inline')

    count = 0
    for btn in expand_box:
        if 'aria-controls' in btn.attrs:
            break
        count+=1


    content = []
    for accomp in accomp_expand:
        ActionChains(driver).move_to_element(accomp).perform()
        time.sleep(1)
        #accomp.click() # <- not working
        driver.execute_script('arguments[0].click();', accomp)

        expand_btn = driver.find_elements_by_class_name('pv-profile-section__see-more-inline')[count:]
        for btn in expand_btn:
            try:
                ActionChains(driver).move_to_element(btn).perform()
                time.sleep(1)
                # btn.click() # <- not working
                driver.execute_script('arguments[0].click();', btn)
            except:
                pass

        soup = bs4.BeautifulSoup(driver.page_source,'html.parser')

        class_block = soup.find_all('li',{'class':'pv-accomplishment-entity--expanded'})

        title = '.pv-accomplishment-entity__title'
        date = '.pv-accomplishment-entity__date'
        issuer = '.pv-accomplishment-entity__issuer'
        description = '.pv-accomplishment-entity__description'

        cont = []
        for item in class_block:
            cont.append({
                'title':text_or_default_accomp(item,title),
                'subtitle':{'date':text_or_default_accomp(item,date),'issuer':text_or_default_accomp(item,issuer)},
               'description':text_or_default_accomp(item,description)
            })

        content.append(cont)


    result = zip(classification,content)
    return list(result)


def open_more():
    eles= driver.find_elements_by_css_selector('.lt-line-clamp__more')
    for ele in eles:
        try:
            driver.execute_script('arguments[0].disabled = true;',ele)
            driver.execute_script('arguments[0].click();',ele)
        except:
            pass



def flatten_list(l):
    return [item for sublist in l for item in sublist]

def one_or_default(element, selector, default=None):
    """Return the first found element with a given css selector
    Params:
        - element {beautifulsoup element}: element to be searched
        - selector {str}: css selector to search for
        - default {any}: default return value
    Returns:
        beautifulsoup element if match is found, otherwise return the default
        ne_or_default(element, selector, default=None)
    """
    try:
        el = element.select_one(selector)
        if not el:
            return default
        return element.select_one(selector)
    except Exception as e:
        return default

def text_or_default(element, selector, default=None):
    """Same as one_or_default, except it returns stripped text contents of the found element
    """
    try:
        return element.select_one(selector).get_text().strip()
    except Exception as e:
        return default

def all_or_default(element, selector, default=[]):
    """Get all matching elements for a css selector within an element
    Params:
        - element: beautifulsoup element to search
        - selector: str css selector to search for
        - default: default value if there is an error or no elements found
    Returns:
        {list}: list of all matching elements if any are found, otherwise return
        the default value
    """
    try:
        elements = element.select(selector)
        if len(elements) == 0:
            return default
        return element.select(selector)
    except Exception as e:
        return default

def get_info(element, mapping, default=None):
    """Turn beautifulsoup element and key->selector dict into a key->value dict
    Args:
        - element: A beautifulsoup element
        - mapping: a dictionary mapping key(str)->css selector(str)
        - default: The defauly value to be given for any key that has a css
        selector that matches no elements
    Returns:
        A dict mapping key to the text content of the first element that matched
        the css selector in the element.  If no matching element is found, the
        key's value will be the default param.
    """
    return {key: text_or_default(element, mapping[key], default=default) for key in mapping}

def get_job_info(job):
    """
    Returns:
        dict of job's title, company, date_range, location, description
    """
    multiple_positions = all_or_default(
        job, '.pv-entity__role-details-container')

    # Handle UI case where user has muttiple consec roles at same company
    if (multiple_positions):
        company = text_or_default(job,
                                  '.pv-entity__company-summary-info > h3 > span:nth-of-type(2)')

        company_href = one_or_default(
            job, 'a[data-control-name="background_details_company"]')['href']
        pattern = re.compile('^/company/.*?/$')
        if pattern.match(company_href):
            li_company_url = 'https://www.linkedin.com/' + company_href
        else:
            li_company_url = ''
        multiple_positions = list(map(lambda pos: get_info(pos, {
            'title': '.pv-entity__summary-info-v2 > h3 > span:nth-of-type(2)',
            'date_range': '.pv-entity__date-range span:nth-of-type(2)',
            'location': '.pv-entity__location > span:nth-of-type(2)',
            'description': '.pv-entity__description'
        }), multiple_positions))
        for pos in multiple_positions:
            pos['company'] = company
            pos['li_company_url'] = li_company_url

        return multiple_positions

    else:
        job_info = get_info(job, {
            'title': '.pv-entity__summary-info h3:nth-of-type(1)',
            'company': '.pv-entity__secondary-title',
            'date_range': '.pv-entity__date-range span:nth-of-type(2)',
            'location': '.pv-entity__location span:nth-of-type(2)',
            'description': '.pv-entity__description',
        })
        company_href = one_or_default(
            job, 'a[data-control-name="background_details_company"]')['href']
        pattern = re.compile('^/company/.*?/$')
        if pattern.match(company_href):
            job_info['li_company_url'] = 'https://www.linkedin.com' + company_href
        else:
            job_info['li_company_url'] = ''

        return [job_info]

def get_school_info(school):
    """
    Returns:
        dict of school name, degree, grades, field_of_study, date_range, &
        extra-curricular activities
    """
    return get_info(school, {
        'name': '.pv-entity__school-name',
        'degree': '.pv-entity__degree-name span:nth-of-type(2)',
        'grades': '.pv-entity__grade span:nth-of-type(2)',
        'field_of_study': '.pv-entity__fos span:nth-of-type(2)',
        'date_range': '.pv-entity__dates span:nth-of-type(2)',
        'activities': '.activities-societies'
    })

def get_volunteer_info(exp):
    """
    Returns:
        dict of title, company, date_range, location, cause, & description
    """
    return get_info(exp, {
        'title': '.pv-entity__summary-info h3:nth-of-type(1)',
        'company': '.pv-entity__secondary-title',
        'date_range': '.pv-entity__date-range span:nth-of-type(2)',
        'location': '.pv-entity__location span:nth-of-type(2)',
        'cause': '.pv-entity__cause span:nth-of-type(2)',
        'description': '.pv-entity__description'
    })

def get_skill_info(skill):
    """
    Returns:
        dict of skill name and # of endorsements
    """
    return get_info(skill, {
        'name': '.pv-skill-category-entity__name',
        'endorsements': '.pv-skill-category-entity__endorsement-count'
    }, default=0)

def personal_info(soup):
        """Return dict of personal info about the user"""
        top_card = one_or_default(soup, 'section.pv-top-card-section')
        contact_info = one_or_default(soup, '.pv-contact-info')

        personal_info = get_info(top_card, {
            'name': '.pv-top-card-section__name',
            'headline': '.pv-top-card-section__headline',
            'company': '.pv-top-card-v2-section__company-name',
            'school': '.pv-top-card-v2-section__school-name',
            'location': '.pv-top-card-section__location',
            'summary': 'p.pv-top-card-section__summary-text'
        })

        image_div = one_or_default(top_card, '.profile-photo-edit__preview')
        image_url = ''
        # print(image_div)
        if image_div:
            image_url = image_div['src']
        else:
            image_div = one_or_default(top_card, '.pv-top-card-section__photo')
            style_string = image_div['style']
            pattern = re.compile('background-image: url\("(.*?)"')
            matches = pattern.match(style_string)
            if matches:
                image_url = matches.groups()[0]

        personal_info['image'] = image_url

        return personal_info

def experiences(soup):
        """
        Returns:
            dict of person's professional experiences.  These include:
                - Jobs
                - Education
                - Volunteer Experiences
        """
        experiences = {}
        container = one_or_default(soup, '.background-section')

        jobs = all_or_default(
            container, '#experience-section ul .pv-position-entity')
        jobs = list(map(get_job_info, jobs))
        jobs = flatten_list(jobs)

        experiences['jobs'] = jobs

        schools = all_or_default(
            container, '#education-section .pv-education-entity')
        schools = list(map(get_school_info, schools))
        experiences['education'] = schools

        volunteering = all_or_default(
            container, '.pv-profile-section.volunteering-section .pv-volunteering-entity')
        volunteering = list(map(get_volunteer_info, volunteering))
        experiences['volunteering'] = volunteering

        return experiences

def skills(soup):
        """
        Returns:
            list of skills {name: str, endorsements: int} in decreasing order of
            endorsement quantity.
        """
        skills = soup.select('.pv-skill-category-entity__skill-wrapper')
        skills = list(map(get_skill_info, skills))

        # Sort skills based on endorsements.  If the person has no endorsements
        def sort_skills(x): return int(
            x['endorsements'].replace('+', '')) if x['endorsements'] else 0
        return sorted(skills, key=sort_skills, reverse=True)

def recommendations():
    tab = driver.find_elements_by_tag_name('artdeco-tab')
    if tab is None:
        logging.warning('Not found.')
        return []
    else:
        expand = driver.find_elements_by_class_name('pv-profile-section__see-more-inline')
        #'show more' btn in the first tab item was clicked in scroll_to_bottom, we only need to click the 'show more' in the other items
        for item in tab[1:]:
            ActionChains(driver).move_to_element(item).perform()
            driver.execute_script('arguments[0].click();',item)
            for btn in expand:
                try:
                    ActionChains(driver).move_to_element(btn).perform()
                    driver.execute_script('arguments[0].click();',btn)
                except:
                    pass

        more = driver.find_elements_by_class_name('lt-line-clamp__more')

        for item in tab:
            ActionChains(driver).move_to_element(item).perform()
            driver.execute_script('arguments[0].click();',item)
            for btn in more:
                try:
                    ActionChains(driver).move_to_element(btn).perform()
                    driver.execute_script('arguments[0].click();',btn)
                except:
                    pass

        soup = bs4.BeautifulSoup(driver.page_source,'html.parser')
        recom = soup.find_all('artdeco-tabpanel')


        recommend = []
        for panel in recom:
            recom_box = panel.find(
                'ul', {'class':'section-info'})

            recom = []

            if recom_box is None:
                recommend.append([])
                continue
            else:
                recom_list = recom_box.find_all(
                    'li',{'class':'pv-recommendation-entity'})

                for item in recom_list:

                    giver_intro = item.find(
                        'div', {'class':'pv-recommendation-entity__detail'}).get_text().strip().split('\n')

                    giver_name = giver_intro[0].strip()
                    giver_job = giver_intro[1].strip()
                    companian_time = giver_intro[3].strip()

                    giver_img = 'https://www.linkedin.com'+item.find(
                        'a', {'data-control-name':'recommendation_details_profile'})['href']

                    giver_recom = item.find(
                        'blockquote', {'class':'pv-recommendation-entity__text relative'}).get_text().strip().split('\n')[0].strip()

                    recom.append({
                        'header':{
                            'name': giver_name,
                            'job': giver_job,
                            'companiam_time':companian_time,
                            'img':giver_img
                        },
                        'recommend':giver_recom
                    })

                recommend.append(recom)

        classification = ['Received','Given']
        result = zip(classification,recommend)
        return list(result)

if __name__ == '__main__':
    # self = sys.modules[__name__]

    # LOGIN
    driver = login('3168095199@qq.com', 'shelock007', proxies={"socksProxy": "127.0.0.1:1080"})


    record = {}

    # GET INTERESTS DETAILS
    interests_data = open_interest('')
    record.update({'interests': interests_data})

    # GET CONTACT DETAILS
    contact_data = open_contact('')
    record.update({'contact': contact_data})


    # PROCEDURE
    # 6496184579081138176
    scroll_to_bottom(contact_url='')

    # GET ACCOMPLISHMENTS DETAILS
    accomplishments_data = open_accomplishments()
    record.update({'accomplishments': accomplishments_data})

    # GET RECOMMENDATIONS
    recommendations_data = recommendations()
    record.update({'recommendations':recommendations_data})

    # OPEN MORE
    open_more()

    # MAKE SOUP
    soup = bs4.BeautifulSoup(driver.page_source, 'html.parser')
    personal_info_data = personal_info(soup)
    record.update({'personal_info': personal_info_data})

    experiences_data = experiences(soup)
    record.update({'experiences': experiences_data})

    skills_data = skills(soup)
    record.update({'skills': skills_data})

    driver.quit()

    print(record)