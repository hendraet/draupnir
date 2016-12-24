import telepot
import time
import praw
import re
import urllib
import sys
import datetime

#----------------------------------Main Class---------------------------------
class Draupnir:

    IIMGUR_PATTERN = re.compile("((http)|(https))(:\/\/i\.imgur\.com\/).*")
    IMGUR_PATTERN = re.compile("((http)|(https))(:\/\/imgur\.com\/).*")
    IREDDIT_PATTERN = re.compile("((http)|(https))(:\/\/i\.redd\.it\/).*")
    REDDIT_UPLOADS_PATTERN = re.compile("((http)|(https))(:\/\/i\.reddituploads\.com\/).*")
    GIF_PATTERN = re.compile(".*(\.gif$)")
    GIFV_PATTERN = re.compile(".*(\.gifv$)")
    JPG_PATTERN = re.compile(".*(\.jpg)")
    DEFAULT_METHOD = "hot"

    #-----------------------------Init----------------------------------------
    def __init__(self):
        self.read_config()

        self.reddit = praw.Reddit(user_agent=self.USER_AGENT, client_id=self.CLIENT_ID, client_secret=self.CLIENT_SECRET)
        self.bot = telepot.Bot(self.TOKEN)

    def start(self, arg_list):
        print(arg_list)
        if len(arg_list) > 1 and arg_list[1] == "daily":
            self.send_special()
        else:
            try:
                self.bot.message_loop(self.handle)
                while 1:
                    time.sleep(10)
            except KeyboardInterrupt:
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

    #-----------------------------General--------------------------------------
    def is_subreddit(self, subreddit_string):
        subreddits = []
        try:
            for s in self.reddit.subreddits.search_by_name(subreddit_string, exact=True):
                subreddits.append(s)
            if subreddits:
                return True
            else:
                return False
        except:
            return False

    def parse_url(self, url):
        if self.IIMGUR_PATTERN.match(url) == None and self.IREDDIT_PATTERN.match(url) == None and self.REDDIT_UPLOADS_PATTERN.match(url) == None:
            return None
        elif self.GIF_PATTERN.match(url):
            return (url, ".gif")
        elif self.GIFV_PATTERN.match(url):
            new_url = re.sub("gifv", "gif", url)
            return (new_url, ".gif")
        elif self.JPG_PATTERN.match(url):
            return (url, ".jpg")
        else:
            return (url, ".jpg")

    def generate_hot_image_list(self, subreddit):
        return subreddit.hot(limit=10)

    def generate_top_image_list(self, subreddit):
        return subreddit.top(limit=10, time_filter="day")

    def generate_images_for_subreddit(self, subreddit_string, method):
        subreddit = self.reddit.subreddit(subreddit_string)
        self.image_list = []

        if method == "top":
            raw_image_list = self.generate_top_image_list(subreddit)
        else:
            raw_image_list = self.generate_hot_image_list(subreddit)
        
        for sub in raw_image_list:
            output = self.parse_url(str(sub.url))
            if output != None:
                self.image_list.append(output)
            if len(self.image_list) >= 3:
                break;

        if self.image_list:
            print(len(self.image_list), self.image_list[0])
            return True
        else:
            return False

    def send_image_for_subreddit(self, subreddit, chat_id, method):
        if self.is_subreddit(subreddit) != False:
            got_images = self.generate_images_for_subreddit(subreddit, method)

            if got_images == True:
                filetype = self.image_list[0][1]
                print(filetype)
                image = urllib.urlopen(self.image_list[0][0])
                print("Done opening")

                if filetype == ".gif":
                    self.bot.sendDocument(chat_id, (subreddit + filetype, image))
                elif filetype == ".jpg":
                    self.bot.sendPhoto(chat_id, (subreddit + filetype, image))
                else:
                    self.bot.sendMessage(chat_id, "Can't send file because filetype is unknown")
                    print("Don't know how to send this")
                print("Done sending")
            else:
                self.bot.sendMessage(chat_id, "Couldn't load any images from this subreddit")
                print("Couldn't load any images")

        else:
            self.bot.sendMessage(chat_id, "No subreddits with this name")
            print("No subreddits with this name")

    def parse_message(self, message):
        message = message.lstrip("/")
        arg_list = message.split("/")
        if len(arg_list) == 2 and (arg_list[1] == "hot" or arg_list[1] == "top"):
            return arg_list[0], arg_list[1]
        else:
            return arg_list[0], self.DEFAULT_METHOD 

    #------------------------------Daily/Special---------------------------------
    def send_special(self):
        chat_list = open("chatlist.txt", "r")
        for line in chat_list.readlines():
            line = line.rstrip()
            chat_id, subreddit = line.split(":")
            self.send_image_for_subreddit(subreddit, chat_id)

    #------------------------------Normal Handle---------------------------------
    def handle(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        print(chat_id)
        self.parse_message(msg["text"])
        caption, method = self.parse_message(msg["text"])
        print(caption, method)

        self.send_image_for_subreddit(caption, chat_id, method)

#------------------------------------------------------------------

#------------------------------Main--------------------------------
def main(arg_list):
    draupnir = Draupnir()
    draupnir.start(arg_list)

if __name__ == "__main__":
    main(sys.argv)
