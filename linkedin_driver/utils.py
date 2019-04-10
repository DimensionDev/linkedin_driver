import re
import bs4
import time
import urllib
import logging

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait

from linkedin_driver import __site_url__
import time

def scroll_slowly_down(driver, by=500):
    height = driver.execute_script("return document.body.scrollHeight")

    for i in range(height//by):
        time.sleep(0.5)
        driver.execute_script('window.scrollBy(0, {})'.format(by))

def filter_contacts(driver, keyword):

    driver.get(
        'https://www.linkedin.com/search/results/people/?keywords={query}&origin=GLOBAL_SEARCH_HEADER'.format(
            query=keyword
        )
    )

    scroll_slowly_down(driver)
    element = WebDriverWait(driver, 10).until(lambda x: x.find_element_by_class_name("artdeco-pagination"))

    while True:

        def has_next():
            soup = bs4.BeautifulSoup(driver.page_source, 'html.parser')

            if soup.find(
                    'button', {
                        'class': 'artdeco-pagination__button--next'}) is not None:
                return soup
            else:
                return None

        next_soup = has_next()

        if next_soup is None:
            print('ダメ')
            break

        contacts = next_soup.find_all('div', {'class': 'search-result__wrapper'})

        for contact in contacts:

            a = contact.find('a', {'class': 'search-result__result-link'})
            if a is not None:
                url = __site_url__ + a.attrs.get('href')
            else:
                url = None

            img = contact.find('img', {'class': 'presence-entity__image'})
            if img is not None:
                image_url = img.attrs.get('src')
            else:
                image_url = None

            link = contact.find('a', {'data-control-name': 'search_srp_result'})
            status = None
            if link is not None:
                link =  __site_url__ + link.attrs['href']
                if hasattr(link, 'text'):
                    status = link.text.strip()

            name = contact.find('span', {'class': 'actor-name'})
            if name is not None:
                name = name.text

            role = contact.find('p', {'class': 'subline-level-1'})
            if role is not None:
                role = role.text

            location = contact.find('p', {'class': 'subline-level-2'})
            if location is not None:
                location = location.text.strip()

            snippets = contact.find('p', {'class': 'search-result__snippets'})
            if snippets is not None:
                snippets = snippets.text.strip()

            mutual_connections = contact.find('a', {'data-control-name': 'view_mutual_connections'})
            mutual_connections_url = None
            highlighted_connections = None
            mutual_connections_count = None
            if mutual_connections is not None:
                mutual_connections_url = __site_url__ + mutual_connections.attrs['href']

                mutual_connections_count = mutual_connections.find('span', {'class': 'search-result__social-proof-count'})
                if mutual_connections_count is not None:
                    mutual_connections_count = mutual_connections_count.text.strip()

                highlighted_connections = mutual_connections.find('li', {'class': 'ivm-entity-pile__img-item--stacked'})
                if highlighted_connections is not None:
                    all_highlighted_connections = highlighted_connections.find_all('img')
                    highlighted_connections = [
                        {'name': connection.attrs.get('alt'),
                         'photo_url': __site_url__ + (connection.attrs.get('src') or ''),}
                        for connection in all_highlighted_connections]

            yield({'url': url,
                   'name': name,
                   'image_url': image_url,
                   'status': status,
                   'link': link,
                   'location': location,
                   'snippets': snippets,
                   'role': role,
                   'mutual_connections': {
                       'count': mutual_connections_count,
                       'highlighted_connections': highlighted_connections,
                       'mutual_connections_url': mutual_connections_url }})


        driver.find_element_by_class_name('artdeco-pagination__button--next').click()

        scroll_slowly_down(driver)
        element = WebDriverWait(driver, 10).until(lambda x: x.find_element_by_class_name("artdeco-pagination"))


def open_contact(driver, contact_url):
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

    ph = []
    phone = contact_soup.find('section',{'class':'pv-contact-info__contact-type ci-phone'})
    if phone is not None:
        phone_content = phone.get_text().strip().split('\n')
        phone_type = phone_content[4].strip()
        phone_number = phone_content[3].strip()
        ph.append({'phone_type':phone_type,'phone_number':phone_number})
       # ph.append(phone_content)
    else:
        phone = None

    address = contact_soup.find('section',{'class':'pv-contact-info__contact-type ci-address'})
    if address is not None:
        address_content = address.text.strip().split('\n')[3].strip()
    else:
        address_content = None

    email = contact_soup.find('section',{'class':'pv-contact-info__contact-type ci-email'})
    if email is not None:
        email_address = email.text.strip().split('\n')[3].strip()
    else:
        email_address = None

    IM_cont = []
    IM = contact_soup.find('section',{'class':'pv-contact-info__contact-type ci-ims'})
    if IM is not None:
        IM_content = IM.get_text().strip().split('\n')
        IM_type = IM_content[6].strip().strip()
        IM_account = IM_content[4].strip()
        IM_cont.append({'IM_type':IM_type,'IM_account':IM_account})
       # IM_cont.append(IM_content)

    birthday = contact_soup.find('section',{'class':'pv-contact-info__contact-type ci-birthday'})
    if birthday is not None:
        birth = birthday.text.strip().split('\n')[2].strip()
    else:
        birth = None


    contact = {"profile_url": profile_url, "websites": websites,"twitter":twitter_url,"phone":ph,"address":address_content
               ,"email":email_address,"IM":IM_cont,"birthday":birth}

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


def scroll_to_bottom(driver, contact_url):
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


def open_interest(driver, contact_url):
    '''if it crashes, try it several times'''

    driver.get(urllib.parse.urljoin(contact_url, 'detail/interests'))
    #driver.get(urllib.parse.urljoin(contact_url, 'detail/interests/companies/'))

    soup = bs4.BeautifulSoup(driver.page_source, 'html.parser')

    interest_searcher = soup.find_all('a',{'class':'pv-profile-detail__nav-link'})

    interest_selector = driver.find_elements_by_class_name('pv-profile-detail__nav-link')

    interests = []

    def extract_interest(soup):
        '''
        helper function to extract each interest
        '''
        box = []
        for item in soup.find_all('li',{'class' : 'entity-list-item'}):
            box.append({
                'img': (item.find('img',{"src":True}) or {}).get('src'),
                'name':item.find('span',{'class':'pv-entity__summary-title-text'}).text,
                'number of followers':item.find('p',{'class':'pv-entity__follower-count'}).text.split(" ")[0]
            })
        return box

    classification = []
    for i in range(len(interest_searcher)):
        classification.append(interest_searcher[i].text.strip().split('\n')[0])
        try:
            interest_selector[i].click()
        except:
            pass

        try:
            current_len = 0
            name_set = set()
            while True:
                list_wrapper=driver.find_element_by_xpath('//div[@class="entity-list-wrapper ember-view"]//a')
                list_wrapper.send_keys(Keys.END)
                time.sleep(5)

                soup = bs4.BeautifulSoup(driver.page_source, 'html.parser')
                name_list = soup.find_all('li',{'class' : 'entity-list-item'})

                last_name = name_list[-1].find('span',{'class':'pv-entity__summary-title-text'}).text
                if last_name in name_set:
                    soup = bs4.BeautifulSoup(driver.page_source, 'html.parser')
                    interests.append(extract_interest(soup))
                    break

                for item in name_list:
                    item_name = item.find('span',{'class':'pv-entity__summary-title-text'}).text
                    name_set.add(item_name)
        except:
            pass

   # classification = ['companies','groups','schools']
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


def open_accomplishments(driver):

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


def open_more(driver):
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

def recommendations(driver):
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

def get_people_viewed(driver):
    viewed = driver.find_elements_by_class_name('pv-browsemap-section__member-container')

    if viewed is None or viewed == []:
        return []
    else:
        ActionChains(driver).move_to_element(viewed[0]).perform()
        soup = bs4.BeautifulSoup(driver.page_source,'html.parser')
        viewed_list = soup.find_all('li',{'class':'pv-browsemap-section__member-container'})
        viewed_info = []
        for item in viewed_list:
            name = item.find('span',{'class':'name actor-name'}).text
            url = 'https://www.linkedin.com'+item.find('a',{'class':'pv-browsemap-section__member ember-view'})['href']
            headline = item.find('p',{'class':'browsemap-headline'}).text
            viewed_info.append({
                'name': name,
                'url':url,
                'headline':headline
            })

        return viewed_info
