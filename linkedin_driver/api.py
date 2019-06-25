from metatype import Dict

from linkedin_driver import _login, __site_url__

from linkedin_driver.utils import (
    open_contact,
    scroll_to_bottom,
    open_interest,
    text_or_default_accomp,
    open_accomplishments,
    flatten_list,
    one_or_default,
    text_or_default,
    all_or_default,
    get_info,
    get_job_info,
    get_school_info,
    get_volunteer_info,
    get_skill_info,
    personal_info,
    experiences,
    skills,
    recommendations,
    get_people_viewed,
    open_more
)

from linkedin_driver.utils import (
    filter_contacts
)

from selenium.webdriver.support.wait import WebDriverWait

from selenium.webdriver.common.action_chains import ActionChains

from selenium.webdriver.common.keys import Keys
# misc
import bs4
import time
import base64
import datetime
import metawiki
import requests
import random
import tqdm

class Contact(Dict):

    messages = []

    @classmethod
    def _get(cls, url, drive, only_contact=False):

        record = {}
        record['@'] = drive.spec + cls.__name__
        record['-'] = url

        if only_contact:
            # CONTACT
            contact_data = open_contact(drive, url)
            record.update({'contact': contact_data})

            obj = cls(record)
            obj.drive = drive
            return obj

        # INTERESTS
        interests_data = open_interest(drive, url)
        record.update({'interests': interests_data})

        # CONTACT
        contact_data = open_contact(drive, url)
        record.update({'contact': contact_data})

        # <<SCROLL-DOWN>>
        scroll_to_bottom(drive, contact_url=url)

        # ACCOMPLISHMENTS
        accomplishments_data = open_accomplishments(drive)
        record.update({'accomplishments': accomplishments_data})

        # RECOMMENDATIONS
        recommendations_data = recommendations(drive)
        record.update({'recommendations':recommendations_data})

        # <<EXPAND-TABS>>
        open_more(drive)

        # PERSONAL-INFO
        soup = bs4.BeautifulSoup(drive.page_source, 'html.parser')
        personal_info_data = personal_info(soup)
        record.update({'personal_info': personal_info_data})

        # EXPERIENCES
        experiences_data = experiences(soup)
        record.update({'experiences': experiences_data})

        # SKILLS
        skills_data = skills(soup)
        record.update({'skills': skills_data})

        # People_who_viewed
        viewed = get_people_viewed(drive)
        record.update({'people_viewed':viewed})

        # END
        obj = cls(record)
        obj.drive = drive
        return obj

    @classmethod
    def _xfilter(cls, drive, keyword=None):
        '''
        Returns:
            Iterator that goes through linked-in search in general.

        TBD: Later to merge with ._filter, which now only returns personal contacts.
        '''
        for item in filter_contacts(drive, keyword):
            item['@'] = drive.spec + cls.__name__
            yield(cls(item))

    @classmethod
    def _filter(cls, drive, limit=None, close_after_execution=True, delay_seconds=20, delay_variance=2):

        print("Please, wait for a few minutes to initialize...")

        existing = set()

        with tqdm.tqdm() as pbar:

            drive.get('https://linkedin.com')
            time.sleep(0.1)
            drive.find_element_by_class_name('nav-item--mynetwork').click()
            time.sleep(delay_seconds+delay_variance*random.random())
            drive.find_element_by_class_name('mn-community-summary__link').click()
            time.sleep(delay_seconds+delay_variance*random.random())

            temp = None

            while True:
                message_list = drive.find_elements_by_class_name('list-style-none')
                last_item = message_list[-1]
                if temp == last_item:
                    break
                temp = last_item
                drive.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(delay_seconds+delay_variance*random.random())


                # TBD: Later make the soup parse only new html loaded.
                soup = bs4.BeautifulSoup(drive.page_source, 'html.parser')
                contact_list = soup.find_all('li',{'class':'list-style-none'})

                for item in contact_list:
                    url = 'https://www.linkedin.com'+item.find_all('a',{'class':'mn-connection-card__link ember-view'})[0].attrs['href']

                    # Because we're now parsing the whole page after each reload.
                    if url in existing:
                        continue
                    else:
                        existing.add(url)

                    name = item.find('span',{'class':'mn-connection-card__name'}).get_text().strip()
                    occupation = item.find('span',{'class':'mn-connection-card__occupation'}).get_text().strip()
                    connect_time = item.find('time',{'class':'time-badge'}).get_text().strip()

                    pbar.update(1)

                    yield cls({
                        '@': drive.spec + cls.__name__,
                        '-': url,
                        'name': name,
                        'occupation': occupation,
                        'connect_time': connect_time})

    def send_message(self, text):
       friend = self['contact']['profile_url'][0]

       self.drive.get(friend)
       get_friend =  self.drive.find_element_by_class_name('pv-s-profile-actions__label')
       ActionChains(self.drive).move_to_element(get_friend).perform()
       time.sleep(1)
       self.drive.execute_script('arguments[0].click();', get_friend)
      # friends = drive.find_element_by_class_name('msg-connections-typeahead__added-recipients')
      # friends.send_keys(friend)
       field = self.drive.find_element_by_class_name('msg-form__message-texteditor')
       ActionChains(self.drive).move_to_element(field).send_keys_to_element(field,text).perform()
       #field = self.drive.execute_script("document.getElementsByClassName('msg-form__message-texteditor').value ='hi';")
       try:
           self.drive.switch_to.active_element.submit()

       except:
            button1 = self.drive.find_element_by_class_name('msg-form__send-button')
            ActionChains(self.drive).move_to_element(button1).perform()
            time.sleep(1)
            self.drive.execute_script('arguments[0].click();', button1)

    def get_message(self):
        friend = self['contact']['profile_url'][0]

        self.drive.get(friend)
        get_friend = self.drive.find_element_by_class_name('pv-s-profile-actions__label')
        ActionChains(self.drive).move_to_element(get_friend).perform()
        import time
        time.sleep(1)

        self.drive.execute_script('arguments[0].click();', get_friend)

        time.sleep(5)
        temp = None
        while True:
            message_list = self.drive.find_elements_by_class_name('msg-s-message-list__event')
            last_item = message_list[0]
            if temp == last_item:
                break
            temp = last_item
            self.drive.execute_script("arguments[0].scrollIntoView(true);", last_item)
            time.sleep(5)

        soup = bs4.BeautifulSoup(self.drive.page_source, 'html.parser')
        message_box = soup.find_all('li',{'class':'msg-s-message-list__event clearfix'})

        week = ''
        time = ''
        for message in message_box:
            if message.find('time',{'class':'msg-s-message-list__time-heading'}) is not None:
                week = message.find('time',{'class':'msg-s-message-list__time-heading'}).get_text().split('\n')[1].strip()
            ltime = message.find_all('time',{'class':'msg-s-message-group__timestamp'})
            if len(ltime) > 0:
                time = ltime[0].get_text().split('\n')[1].strip()
            context = message.find('p').get_text()
            self.messages.append(Message({'week': week,'time':time,'text': context}))

class Post(Dict):

    @classmethod
    def _get(cls, url, drive=None):
        drive.get(url)
        # extracted data
        record = {}
        if drive is not None:
            record['@'] = drive.spec + cls.__name__
        return cls(record)

    @classmethod
    def _filter(cls, drive, limit=None, close_after_execution=True):

        drive.get(__site_url__)

        while True:

            # click all "show more" links
            eles = drive.find_elements_by_css_selector('.see-more')
            for ele in eles:
                try:
                    drive.execute_script('arguments[0].click();',ele)
                except:
                    pass

            soup = bs4.BeautifulSoup(drive.page_source, 'html.parser')
            posts_placeholder = soup.find('div', {'class': 'core-rail'})
            posts = posts_placeholder.find_all('div', {'class': 'relative ember-view'})

            count = 0

            for i, post in enumerate(posts):

                # url = 'https://www.linkedin.com/feed/update/'+post.attrs['data-id']

                # skip those which appear empty (e.g., "occludable-update")
                if not post.text.strip():
                    print('SKIPPING SOME POST, THAT HAS NO TEXT')
                    continue

                # data_id not in post.attrs anymore
                data_id = post.attrs.get('data-id')

                if data_id is None:
                    v2_id = post.find('div', {'class': 'feed-shared-update-v2'})

                    if v2_id is not None:
                        data_id = v2_id.attrs.get('data-id')

                # skip if could not retrieve data-id anyway.
                if data_id is None:
                    print('SKIPPING SOME POST, THAT HAS NO DATA-ID')
                    continue

                url = 'https://www.linkedin.com/feed/update/'+data_id


                author_status = post.find('div', {'class': 'presence-entity'})
                if author_status:
                    shared_ = author_status.find('div', {'class': 'ivm-view-attr__img--centered'})
                    if shared_:
                        shared_ = shared_.text
                        if shared_:
                            author_status = shared_.strip()
                        else:
                            author_status = author_status.text.strip()
                    else:
                        author_status = author_status.text.strip()

                text = post.find('div', {'class': 'feed-shared-text'})
                if text is not None:
                    if isinstance(text, str):
                        text = text.strip()
                    else:
                        text = text.text.strip()
                else:
                    text = None

                # ???
                mentioned_by = post.find('a', {'class': 'feed-shared-text-view__mention'})
                if mentioned_by:
                    profile_path = mentioned_by.attrs.get('href')
                    if profile_path:
                        mentioned_by = 'https://www.linkedin.com'+profile_path

                author_image = post.find('img', {'class': 'presence-entity__image'})
                if author_image is not None:
                    author_image = author_image.attrs.get('src')
                else:
                    author_image = None

                post_image = post.find('img', {'class': 'feed-shared-article__image'})
                if post_image is not None:
                    post_image = post_image.attrs.get('src')
                else:
                    post_image = None

                if author_image is not None:
                    author_image_data = requests.get(author_image)
                    if author_image_data.ok:
                        author_image_data = str(base64.b64encode(author_image_data.content), 'ascii')
                    else:
                        author_image_data = None
                else:
                    author_image_data = None

                if post_image is not None:
                    post_image_data = requests.get(post_image)
                    if post_image_data.ok:
                        post_image_data = str(base64.b64encode(post_image_data.content), 'ascii')
                    else:
                        post_image_data = None
                else:
                    post_image_data = None


                media_title = post.find('div', {'class': 'feed-shared-article__description-container'})
                media_subtitle = None

                if media_title is not None:
                    title = media_title.find('span')
                    subtitle = media_title.find('h3', {'class': 'feed-shared-article__subtitle'})

                    if title is not None:
                        media_title = title.text.strip()
                    else:
                        media_title = None

                    if subtitle is not None:
                        media_subtitle = subtitle.text.strip()
                    else:
                        media_subtitle = None

                media_link = post.find('a', {'class': 'app-aware-link'})
                if media_link is not None:
                    media_link = media_link.attrs['href']


                counts_ul = post.find('ul', {'class': 'feed-shared-social-counts'})
                media_counts = {}

                if counts_ul is not None:
                    counts_li = counts_ul.find_all('li')
                else:
                    counts_li = []

                for _count in counts_li:
                    cnt = _count.find('span', {'class': 'visually-hidden'})
                    if cnt is not None:

                        if 'Likes' in cnt.text:
                            media_counts.update({'likes_count': int(cnt.text.split('Likes')[0].strip().replace(',',''))})

                        if 'Comments' in cnt.text:
                            media_counts.update({'comments_count': int(cnt.text.split('Comments')[0].strip().replace(',',''))})

                        if 'Views' in cnt.text:
                            media_counts.update({'views_count': int(cnt.text.split('Views')[0].strip().replace(',',''))})


                item = {
                    'url': url,
                    'date': None,
                    'body': text,
                    'media': {
                        'author_image': author_image,
                        'post_image': post_image,
                        'author_image_data': author_image_data,
                        'post_image_data': post_image_data,
                        'media_link': media_link,
                        'media_title': media_title,
                        'media_subtitle': media_subtitle
                    },
                    'stats': media_counts,
                    'mentioned_by': mentioned_by,
                    'author_status': author_status,
                    'logged': datetime.datetime.utcnow().isoformat(),
                    '-': url,
                    '+': metawiki.name_to_url(drive.metaname) if drive.metaname else '',
                    '*': metawiki.name_to_url('::mindey/topic#linkedin'),
                    '@': drive.spec + cls.__name__
                }


                count += 1
                yield cls(item)

                if limit:
                    if count >= limit:
                        break

            drive.execute_script("window.scrollTo(0, document.body.scrollHeight);")


    def _update(self):
        raise NotImplemented

    def add_comment(self, drive, text):
        field = drive.find_element_by_class_name('mentions-texteditor__contenteditable')
        field.send_keys(text)
        button = drive.find_element_by_class_name('comments-comment-box__submit-button')
        button.click()



class Message(Dict):

    @classmethod
    def _get(cls, url, drive=None):
        drive.get(url)
        # extracted data
        record = {}
        if drive is not None:
            record['@'] = drive.spec + cls.__name__
        return cls(record)

    def _update(self):
        raise NotImplemented


class Comment(Dict):

    @classmethod
    def _get(self):
        raise NotImplemented

    @classmethod
    def _filter(self):
        raise NotImplemented

    def _update(self):
        raise NotImplemented


class PostLike(dict):

    @classmethod
    def _get(self):
        raise NotImplemented

    @classmethod
    def _filter(self):
        raise NotImplemented

    def _update(self):
        raise NotImplemented


class CommentLike(Dict):

    @classmethod
    def _get(self):
        raise NotImplemented

    @classmethod
    def _filter(self):
        raise NotImplemented

    def _update(self):
        raise NotImplemented

