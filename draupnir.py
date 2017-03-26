import telepot
import time
import praw
import re
import urllib.request
import sys
import datetime
import traceback

#----------------------------------Main Class---------------------------------
class Draupnir:

    URL_PATTERN = re.compile("^((http[s]?|ftp):\/)?\/?([^:\/\s]+)((\/\w+)*\/)([\w\-\.]+[^#?\s]+)(.*)?(#[\w\-]+)?$")
    IIMGUR_PATTERN = re.compile("((http)|(https))(:\/\/i\.imgur\.com\/).*")
    IMGUR_PATTERN = re.compile("((http)|(https))(:\/\/imgur\.com\/).*")
    IREDDIT_PATTERN = re.compile("((http)|(https))(:\/\/i\.redd\.it\/).*")
    REDDIT_UPLOADS_PATTERN = re.compile("((http)|(https))(:\/\/i\.reddituploads\.com\/).*")
    GIF_PATTERN = re.compile(".*(\.gif$)")
    GIFV_PATTERN = re.compile(".*(\.gifv$)")
    JPG_PATTERN = re.compile(".*(\.jpg)")
    DEFAULT_METHOD = "hot"
    TOP = [ "all", "year", "month", "week", "day" ]

    #-----------------------------Init----------------------------------------
    def __init__(self):
        self.read_config()

        self.reddit = praw.Reddit(user_agent=self.USER_AGENT, client_id=self.CLIENT_ID, client_secret=self.CLIENT_SECRET)
        self.bot = telepot.Bot(self.TOKEN)

    def start(self, arg_list):
        print("argument list:", arg_list)
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

        if config_dict["DEBUG_CHAT"] == "":
            self.DEBUG_CHAT = ""
            print("No debug chat specified.")
        else:
            self.DEBUG_CHAT = str(config_dict["DEBUG_CHAT"])

    #-----------------------------Logging--------------------------------------

    def search_file(self, f, string):
        for line in f:
            if string in line:
                return True
        return False


    def log_urls(self, url_list):
        logfile = open("urls.log", "w+")
        try:
            for sub in url_list:
                #strip
                if not self.search_file(logfile, sub.url):
                    logfile.write(sub.url + "\n")
        finally:
            logfile.close()


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
            return None

    def generate_hot_image_list(self, subreddit):
        return subreddit.hot(limit=50)

    def generate_top_image_list(self, subreddit):
        return subreddit.top(limit=50, time_filter="all")

    def generate_images_for_subreddit(self, subreddit_string, method):
        subreddit = self.reddit.subreddit(subreddit_string)
        self.image_list = []

        if method == "all":
            raw_image_list = self.generate_top_image_list(subreddit)
        else:
            raw_image_list = self.generate_hot_image_list(subreddit)

        for sub in raw_image_list:
            output = self.parse_url(str(sub.url))
            if output != None:
                self.image_list.append(output)
            if len(self.image_list) >= 5:
                break;

        self.log_urls(raw_image_list)

        print("length of image list:", len(self.image_list))
        if self.image_list:
            print("image url:", self.image_list)
            return True
        else:
            return False

    def send_image_for_subreddit(self, subreddit, chat_id, method):
        if self.is_subreddit(subreddit) != False:
            got_images = self.generate_images_for_subreddit(subreddit, method)

            if got_images == True:

                image = None
                for i in range(0, len(self.image_list)):
                    filetype = self.image_list[i][1]
                    print("filetype:", filetype)
                    try:
                        image = urllib.request.urlopen(self.image_list[i][0])
                    except Exception as e:
                        print(e, "\n" + "Failed opening " + str(i+1) + ". image" )
                        err_type, err_value, err_traceback = sys.exc_info()
                        formatted_traceback = traceback.format_tb(err_traceback)

                        self.bot.sendMessage(self.DEBUG_CHAT, "An error occured\n" +
                                "Couldn't load image\n\n" +
                                formatted_traceback[0] +
                                str(e) + "\n\n" +
                                "Filetype: " + filetype + "\n"
                                "URL: " + self.image_list[i][0])
                        continue
                    break

                if image == None:
                    print("Couldn't open any images")
                    return

                print("Done opening")

                if filetype == ".gif":
                    self.bot.sendDocument(chat_id, (subreddit + filetype, image))
                elif filetype == ".jpg":
                    self.bot.sendPhoto(chat_id, (subreddit + filetype, image))
                else:
                    self.bot.sendMessage(chat_id, "Can't send file because filetype is unknown")
                    print("Can't send file because filetype is unknown")
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
        if len(arg_list) == 2 and (arg_list[1] == "hot" or arg_list[1] == "all" ):
            return arg_list[0], arg_list[1]
        else:
            return arg_list[0], self.DEFAULT_METHOD

    #------------------------------Daily/Special---------------------------------
    def send_special(self):
        chat_list = open("chatlist.txt", "r")
        for line in chat_list.readlines():
            line = line.rstrip()
            chat_id, subreddit = line.split(":")
            self.send_image_for_subreddit(subreddit, chat_id, self.DEFAULT_METHOD)

    #------------------------------Normal Handle---------------------------------
    def handle(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        print("chat_id:", chat_id)
        self.parse_message(msg["text"])
        caption, method = self.parse_message(msg["text"])
        print("subreddit-caption:", caption, "method:", method)

        self.send_image_for_subreddit(caption, chat_id, method)

#------------------------------------------------------------------

#------------------------------Main--------------------------------
def main(arg_list):
    draupnir = Draupnir()
    draupnir.start(arg_list)

if __name__ == "__main__":
    main(sys.argv)
