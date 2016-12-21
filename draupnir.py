import telepot
import time
import praw
import re
import urllib
import sys
import datetime

#----------------------------------Main Class---------------------------------
class Draupnir:

    IMGUR_PATTERN = re.compile("((http)|(https))(:\/\/i\.imgur\.com\/).*")
    IREDDIT_PATTERN = re.compile("((http)|(https))(:\/\/i\.redd\.it\/).*")
    REDDIT_UPLOADS_PATTERN = re.compile("((http)|(https))(:\/\/i\.reddituploads\.com\/).*")
    GIF_PATTERN = re.compile(".*(\.gif$)")
    GIFV_PATTERN = re.compile(".*(\.gifv)")
    JPG_PATTERN = re.compile(".*(\.jpg)")

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
        if self.IMGUR_PATTERN.match(url) == None and self.IREDDIT_PATTERN.match(url) == None and self.REDDIT_UPLOADS_PATTERN.match(url) == None:
            return None
        elif self.GIF_PATTERN.match(url) != None:
            return (url, ".gif")
        elif self.GIFV_PATTERN.match(url) != None:
            new_url = re.sub("gifv", "gif", url)
            return (new_url, ".gif")
        elif self.JPG_PATTERN.match(url) != None:
            return (url, ".jpg")
        else:
            return (url, ".jpg")

    def generate_images_for_subreddit(self, subreddit_string):
        subreddit = self.reddit.subreddit(subreddit_string)
        self.image_list = []

        for sub in subreddit.hot(limit=10):
            output = self.parse_url(str(sub.url))
            if output != None:
                self.image_list.append(output)
            if len(self.image_list) >= 3:
                break;

        print(len(self.image_list), self.image_list[0])

        if self.image_list:
            return True
        else:
            print("No images available")
            return False

    def send_image_for_subreddit(self, subreddit, chat_id):
        if self.is_subreddit(subreddit) != False:
            got_images = self.generate_images_for_subreddit(subreddit)

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
                    print("Don't know how to send this")
                print("Done sending")
            else:
                print("Couldn't load any images")

        else:
            print("No subreddits with this name")

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
        caption = msg["text"].strip("/")

        self.send_image_for_subreddit(caption, chat_id)

#------------------------------------------------------------------

#------------------------------Main--------------------------------
def main(arg_list):
    draupnir = Draupnir()
    draupnir.start(arg_list)

if __name__ == "__main__":
    main(sys.argv)
