import telepot
import time
import praw
import re
import urllib
import sys
import datetime

class Draupnir:

    IMGUR_PATTERN = re.compile("((http)|(https))(:\/\/i\.imgur\.com\/).*")
    IREDDIT_PATTERN = re.compile("((http)|(https))(:\/\/i\.redd\.it\/).*")
    REDDIT_UPLOADS_PATTERN = re.compile("((http)|(https))(:\/\/i\.reddituploads\.com\/).*")
    GIF_PATTERN = re.compile(".*(\.gif[^v])")
    GIFV_PATTERN = re.compile(".*(\.gifv)")
    JPG_PATTERN = re.compile(".*(\.jpg)")

    def __init__(self):
        self.read_config()

        self.reddit = praw.Reddit(user_agent=self.USER_AGENT, client_id=self.CLIENT_ID, client_secret=self.CLIENT_SECRET)
        self.bot = telepot.Bot(self.TOKEN)

    def start(self):
        self.f = open("urls.log", "w")
        try:
            print(self.TOKEN)
            self.bot.message_loop(self.handle)
            while 1:
                time.sleep(10)
        except KeyboardInterrupt:
            self.f.close()
            sys.exit()


    def read_config(self):
        config = open("config.ini", "r")
        lines = config.readlines()
        config_dict = {}

        for line in lines:
            line = line.rstrip()
            key_value = line.split("=")
            config_dict[key_value[0]] = key_value[1]

        try:
            self.TOKEN = config_dict["TOKEN"]
            self.USER_AGENT = str(config_dict["USER_AGENT"])
            self.CLIENT_ID = str(config_dict["CLIENT_ID"])
            self.CLIENT_SECRET = str(config_dict["CLIENT_SECRET"])
        except KeyError:
            print("Malformatted config file")
            sys.exit()

    def writeUrls(self, url_input_list):
        for url in url_input_list:
            self.f.write(url + "\n")

    def is_subreddit(self, subreddit_string):
        subreddits = []
        try:
            for s in self.reddit.subreddits.search_by_name(subreddit_string, exact=True):
                subreddits.append(s)
            if subreddits != []:
                return True
            else:
                return False
        except:
            return False

    def parse_urls(self, url_input_list):
        for url in url_input_list:
            print(url)
            if self.IMGUR_PATTERN.match(url) == None and self.IREDDIT_PATTERN.match(url) == None and self.REDDIT_UPLOADS_PATTERN.match(url) == None:
                continue
            if self.GIF_PATTERN.match(url) != None:
                return (url, ".gif")
            elif self.GIFV_PATTERN.match(url) != None:
                print(url)
                new_url = re.sub("gifv", "gif", url)
                print(new_url)
                return (new_url, ".gif")
            elif self.JPG_PATTERN.match(url) != None:
                return (url, ".jpg")
            else:
                return (url, ",jpg")
        return None


    def generate_image_for_subreddit(self, subreddit_string):
        subreddit = self.reddit.subreddit(subreddit_string)
        url_input_list = []

        for sub in subreddit.hot(limit=10):
            url_input_list.append(str(sub.url))

        if self.f != None:
            self.writeUrls(url_input_list)
        else:
            print("Couldn't write log")

        parsed_url = self.parse_urls(url_input_list)

        if parsed_url != None:
            return urllib.request.urlopen(parsed_url[0]), parsed_url[1]
        else:
            print("No images available")
            return None, None

    def handle(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        caption = msg["text"].strip("/")

        if self.is_subreddit(caption) != False:
            image, filetype = self.generate_image_for_subreddit(caption)
            if image != None:
                if filetype == ".gif":
                    self.bot.sendDocument(chat_id, (caption + filetype, image))
                else:
                    self.bot.sendPhoto(chat_id, (caption + filetype, image))
        else:
            print("No subreddits with this name")

def main():
	draupnir = Draupnir()
	draupnir.start()

if __name__ == "__main__":
	main()
