from metatype import Dict

from linkedin_driver import _login, __site_url__

from linkedin_driver.utils import (
    open_contact,
    scroll_to_bottom,
    open_interest,
    text_or_default_accomp,
    open_accomplishments,
    open_more,
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
    recommendations
)

from linkedin_driver.utils import (
    filter_contacts
)

from selenium.webdriver.support.wait import WebDriverWait

# misc
import bs4
import base64
import datetime
import metawiki
import requests

class Contact(Dict):

    @classmethod
    def _filter(cls, keyword=None, drive=None):
        '''
        Returns:
            Iterator.
        '''
        if not cls._DRIVES:
            if drive is not None:
                cls._DRIVES.append(drive)
            else:
                cls._DRIVES.append(_login())
        else:
            driver = cls._DRIVES[0]

        for item in filter_contacts(driver, keyword):
            yield(cls(item))

        driver.quit()
        raise NotImplemented

    @classmethod
    def _get(cls, url, drive=None):

        if not cls._DRIVES:
            if drive is not None:
                cls._DRIVES.append(drive)
            else:
                cls._DRIVES.append(_login())
        else:
            driver = cls._DRIVES[0]

        record = {}

        # INTERESTS
        interests_data = open_interest(driver, url)
        record.update({'interests': interests_data})

        # CONTACT
        contact_data = open_contact(driver, url)
        record.update({'contact': contact_data})

        # <<SCROLL-DOWN>>
        scroll_to_bottom(driver, contact_url=url)

        # ACCOMPLISHMENTS
        accomplishments_data = open_accomplishments(driver)
        record.update({'accomplishments': accomplishments_data})

        # RECOMMENDATIONS
        recommendations_data = recommendations(driver)
        record.update({'recommendations':recommendations_data})

        # <<EXPAND-TABS>>
        open_more(driver)

        # PERSONAL-INFO
        soup = bs4.BeautifulSoup(driver.page_source, 'html.parser')
        personal_info_data = personal_info(soup)
        record.update({'personal_info': personal_info_data})

        # EXPERIENCES
        experiences_data = experiences(soup)
        record.update({'experiences': experiences_data})

        # SKILLS
        skills_data = skills(soup)
        record.update({'skills': skills_data})

        # END
        driver.quit()

        return cls(record)


    def send_message(self):
        raise NotImplemented


class Post(Dict):

    @classmethod
    def _get(self, url, drive=None):
        if not cls._DRIVES:
            if drive is not None:
                cls._DRIVES.append(drive)
            else:
                cls._DRIVES.append(_login())
        else:
            driver = cls._DRIVES[0]

        driver.get(url)

    @classmethod
    def _filter(cls, drive=None, limit=None, close_after_execution=True):

        if not cls._DRIVES:
            if drive is not None:
                cls._DRIVES.append(drive)
            else:
                cls._DRIVES.append(_login())

        driver = cls._DRIVES[0]

        driver.get(__site_url__)

        while True:

            # click all "show more" links
            eles = driver.find_elements_by_css_selector('.see-more')
            for ele in eles:
                try:
                    driver.execute_script('arguments[0].click();',ele)
                except:
                    pass

            soup = bs4.BeautifulSoup(driver.page_source, 'html.parser')
            posts_placeholder = soup.find('div', {'class': 'core-rail'})
            posts = posts_placeholder.find_all('div', {'class': 'relative ember-view'})

            count = 0

            for i, post in enumerate(posts):

                url = 'https://www.linkedin.com/feed/update/'+post.attrs['data-id']

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
                    '+': metawiki.name_to_url(driver.metaname) if driver.metaname else '',
                    '*': metawiki.name_to_url('::mindey/topic#linkedin')
                }


                count += 1
                yield item

                if limit:
                    if count >= limit:
                        break

            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")


    def _update(self):
        raise NotImplemented

    def add_comment(self, text):
        field = self.driver.find_element_by_class_name('mentions-texteditor__contenteditable')
        field.send_keys(text)
        button = self.driver.find_element_by_class_name('comments-comment-box__submit-button')
        button.click()



class Message(Dict):

    @classmethod
    def _get(self):
        raise NotImplemented

    @classmethod
    def _filter(self):
        raise NotImplemented

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

