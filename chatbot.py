# PA6, CS124, Stanford, Winter 2019
# v.1.0.3
# Original Python code by Ignacio Cases (@cases)
######################################################################
import movielens

import numpy as np
import re
import string
from nltk.stem import PorterStemmer
import random

class Chatbot:
    """Simple class to implement the chat-bot for PA 6."""


    def intro(self):
        return "extract_titles(text) - without quotation marks / correct cap" \
                    "find_movies_by_title(title) - without quotation marks / correct cap, foreign/alternate titles, disambiguation" \
                    "extract_sentiment(text), - fine grained" \
                    " find_movies_closest_to_title(title, max_distance), - spellcheck" \
                    " extract_sentiment_for_movies(text), - multiple movies " \
                    "disambiguate(clarification, candidateIndices)" \
                    "process(line) - respond to arbitrary, questions, emotions, dialogue for spellcheck, disambig, multiple sentiment " \
                    " spelling mistakes are intentional :)"
    def __init__(self, creative=False):
      # The chatbot's default name is `moviebot`. Give your chatbot a new name.

      self.name = 'MovieMaster'
      self.creative = creative
      self.opposite = {'dont', 'didnt', 'wont', 'wasnt', 'werent', 'hasnt', 'cant', 'shouldnt', 'never', 'not', 'hardly', 'seldom', 'rarely', 'cannot'}
      self.strong_words = {'love', 'hate', 'best', 'worst', 'amazing', 'wonderful', 'majestic', 'favorite', 'really', 'very', 'awful', 'terrible', 'cringe', 'awesome'}
      self.stemmer = PorterStemmer()
      # This matrix has the following shape: num_movies x num_users
      # The values stored in each row i and column j is the rating for
      # movie i by user j
      self.titles, ratings = movielens.ratings()
      self.sentiment = movielens.sentiment()
      self.current_ratings = np.zeros(len(self.titles))
      self.k = 5
      self.ratings_given = 0
      self.top_movies = []
      self.pos_response = {"yeah", "yea", "ya", "y", "yes", "ye", "yeet", "yess", "yesss", "yessir", "yes sir", "yes ma'am", "yes mam", "yeeters", "sure", "ok", "okay", "yuh", "yup", "fine", "twist my arm"}
      self.neg_response = {"no", "nah", "na", "n", "nope", "no sir", "no ma'am", "no mam", "negative", "not today", "not", "bye", "cya", "nopers"}

      # creative features
      self.have_another_rec = ["I never thought you'd ask! This movie might be even more perfect for you: \"%s\"",
                               "\"%s\" would make the perfect Netflix and chill vid. ",
                               "I think you are really going to love \"%s\" ",
                               "Based on what you've told me, you should try \"%s\" ",
                               "Wow, you're clearly planning to Netflix binge, aren't you? I think you'd like \"%s\"",
                               "How about \"%s\" ",
                               "You should really be studying for midterms, but \"%s\" would definitely put you"
                               "in the right mood for them. "]
      self.want_another_rec = ["Do you want another recommendation? ",
                               "Need another one? ",
                               "Want another one to procrastinate more? ",
                               "Do you want more movie recs? "]
      self.emotion_lines = {"sad" : ["Aww I hope you feel better soon. ",
                                        "Oy, We all have those days. "
                                        "Merp maybe a great movie could cheer you up? "],
                            "angry": ["I am so so sorry for whatever I did to upset you. ",
                                    "Wow I apologize. Please accept my apology! ",
                                     "I must have done something pretty awful to upset you so. Let's see if I can make it up to you. ",
                                      "Sounds like you're super mad! My taste in movies can't be thaaat bad. "],
                            "scared": ["Don't be scared! I'm right hear with you! ",
                                       "Sometimes I get scared at night, too. ",
                                       "No reason to be fearful. You're totally safe. ",
                                       "The only thing to fear is fear itself. "],
                            "happy": ["Yay! May your days continue to make you so happy! ",
                                      "Wow that's great!",
                                      "That's awesome!"
                                      "Cool!"]}
      self.ask_for_movie = ["Why don't you tell me about a movie you've seen recently? ",
                            "Seen any good movies recently? ",
                            "What's a movie you have strong feelings about. ",
                            "There are so many movies out there. Have any thoughts on them? "]
      self.pivot = ["Let's go back to talking about movies. ",
                    "Maybe we should talk about what I do best: movies. "
                    "Let's talk about movies! "]
      self.clarify = ["I'm sorry, I didn't understand that. ",
                      "I didn't totally understand what you said."]
      self.switch = ["Do you want to tell me more about movies, or do you want to hear some recommendations? ",
                     "Are you ready to hear recommendations, or do you want to teach me more about what you like? "]
      self.dict = {}
      self.active_movie = ""
      self.conversation_point = "collecting"
      self.active_movies_titles = []
      self.emotional_count = 0

      # Binarize the movie ratings before storing the binarized matrix.
      self.ratings = self.binarize(ratings, 2.5)
      #############################################################################
      #                             END OF YOUR CODE                              #
      #############################################################################

    #############################################################################
    # 1. WARM UP REPL                                                           #
    #############################################################################


    def greeting(self):
      """Return a message that the chatbot uses to greet the user."""
      #############################################################################
      # TODO: Write a short greeting message                                      #
      #############################################################################

      greeting_message = "Hi! I\'m %s and I\'m here to help you find some satisfying movies. " \
                         "Want to tell me about some movies that you saw recently?" % self.name

      #############################################################################
      #                             END OF YOUR CODE                              #
      #############################################################################
      return greeting_message

    def goodbye(self):
      """Return a message that the chatbot uses to bid farewell to the user."""
      #############################################################################
      # TODO: Write a short farewell message                                      #
      #############################################################################

      goodbye_message = "Farewell friend... enjoy the movie-watching!"

      #############################################################################
      #                             END OF YOUR CODE                              #
      #############################################################################
      return goodbye_message


    def process(self, line):
        """Process a line of input from the REPL and generate a response.

        This is the method that is called by the REPL loop directly with user input.

        You should delegate most of the work of processing the user's input to
        the helper functions you write later in this class.

        Takes the input string from the REPL and call delegated functions that
            1) extract the relevant information, and
            2) transform the information into a response to the user.

        Example:
          resp = chatbot.process('I loved "The Notebok" so much!!')
          print(resp) // prints 'So you loved "The Notebook", huh?'

        :param line: a user-supplied line of text
        :returns: a string containing the chatbot's response to the user input
        """
        response = ""

        def is_emotional(text):
            anger_regex = re.compile(r"((I|me)[^\"]*(hate|angry|anger|pissed|furious|irate|irritat|exasperat|annoy)[^\"]*)|(You[^\"]*(anger|piss|irritat|exasperat|annoy)[^\"]*me)", re.I)
            happy_regex = re.compile(r"(I|me)[^\"]*(happy|joy|cheer|merry|gleeful)[^\"]*", re.I)
            sad_regex = re.compile(r"((I|me)[^\"]*(sad|depress|miserable|gl[u|oo]m))|(You.*(depress|sadden)[^\"]*me)", re.I)
            scared_regex = re.compile(r"((I|me)[^\"]*(fearful|scared|terrified|worried))|(You.*(scare|terrify|worry|frighten)[^\"]*me)", re.I)
            if re.search(anger_regex, text):
                return "angry"
            elif re.search(happy_regex, text):
                return "happy"
            elif re.search(sad_regex, text):
                return "sad"
            elif re.search(scared_regex, text):
                return "scared"
            else:
                return None

        def is_yn_question(text):
            question_regex = re.compile(r"(?:(?:can)|(?:will)|(?:do)) you (.*)\?", re.I)
            if re.match(question_regex, text):
                return re.match(question_regex, text).group(1)


        if self.creative:
            #print(self.dict)
            #print(self.conversation_point)
            partial_string = ""
            if is_emotional(line):
                self.emotional_count += 1
                emotion = is_emotional(line)
                if self.emotional_count > 3:
                    return "It's possible I'm misreading you talking about a movie as you being %s. " \
                           "Maybe try putting the movie title in quotation marks? " % emotion
                if self.emotional_count > 4:
                    partial_string += "Nope, it seems like you're actually really %s. " % emotion
                self.conversation_point = "switchpoint"
                return partial_string + random.choice(self.emotion_lines[emotion]) + \
                    random.choice(self.pivot) + random.choice(self.switch)
            self.emotional_count = 0
            if is_yn_question(line):
                partial_string += "Sorry, I don't know how to \"%s.\" " % is_yn_question(line)
                partial_string += "All I know how to do is talk about movies. Sorry dude. "
                if self.conversation_point == "collecting" or self.conversatio_point == "confirming name" or self.conversation_point == "confirming sentiment":
                    return partial_string + random.choice(self.pivot) + random.choice(self.ask_for_movie)
                elif conversation_point == "recommending":
                    return partial_string + (random.choice(self.have_another_rec) % self.top_movies.pop(0)[0]) + random.choice(self.want_another_rec)
            if re.match(r".*\?$", line):
                partial_string += "The only question I know how to answer is what movies you'll like. "
                if self.conversation_point == "collecting" or self.conversatio_point == "confirming name" or self.conversation_point == "confirming sentiment":
                    return partial_string + "And to do that, I need more info about your prefs. " + random.choice(self.pivot) + random.choice(self.ask_for_movie)
                elif conversation_point == "recommending":
                    return partial_string + (
                                random.choice(self.have_another_rec) % self.top_movies.pop(0)[0]) + random.choice(
                        self.want_another_rec)
            if self.conversation_point == "switchpoint":
                if re.match(r"rec|switch", line):
                    self.conversation_point = "recommending"
                    partial_string = "Great, I'll start giving you recommendations. "
                    indices_recommended = self.recommend(self.current_ratings, self.ratings, self.k, self.creative)
                    self.top_movies = [self.titles[x] for x in indices_recommended]
                    return partial_string + "Based on what you've told me, I think you will like %s. " % self.top_movies.pop(0)[0] + random.choice(self.want_another_rec)
                else:
                    self.conversation_point = "collecting"
                    return partial_string + random.choice(self.ask_for_movie)
            if self.conversation_point == "recommending":
                if not self.top_movies:
                    return partial_string + "I'm sorry, those are all of my recommendations at the moment. You can enter \
                                    :quit and start over if you want. "
                elif line.lower() in self.pos_response:
                    return partial_string + (random.choice(self.have_another_rec) % self.top_movies.pop(0)[0]) + random.choice(self.want_another_rec)
                elif line.lower() in self.neg_response:
                    return partial_string + "No worries. Type :quit to exit and come back when you're ready for more recommendations. " \
                         "Enjoy the movie-watching! "
                else:
                    return partial_choice + random.choice(self.clarify) + random.choice(self.want_another_rec)
            # extract titles from user input
            if self.conversation_point == "collecting":
                self.active_movies_titles = self.extract_titles(line)
                # ensure movie was captured
                if not self.active_movies_titles:
                    return partial_string + random.choice(self.clarify)
                else:
                    self.conversation_point = "processing"
                    sentiments = self.extract_sentiment_for_movies(line)
                    temp_dict = {}
                    for tup in sentiments:
                        temp_dict[tup[0]] = tup[1]
                    for movie in self.active_movies_titles:
                        self.dict[movie] = [self.find_movies_by_title(movie), temp_dict[movie]]
                    # If statement is "But not x [or y]"
                    butnot_regex = r"^[b|B]ut not"
                    if re.search(butnot_regex, line) and self.dict[self.active_movies_titles[0]][1] == 0:
                        for movie in self.active_movies_titles:
                            if self.dict[movie][1] == 0:
                                self.dict[movie][1] = -self.current_ratings[self.active_movie]
            if self.conversation_point == "confirming name":
                if line.lower() in self.pos_response:
                    right_movie = self.dict[self.active_movie][0][-1]
                    self.dict[self.active_movie][0] = [right_movie]
                    self.conversation_point = "processing"
                    partial_string = "Great. Confirmed that you're talking about %s " % self.titles[right_movie]
                elif line.lower() in self.neg_response:
                    self.dict[self.active_movie][0] = self.dict[self.active_movie][0][:-1]
                    if not self.dict[self.active_movie][0]:
                        self.dict.pop(self.active_movie)
                        partial_string += "I'm giving up on trying to find %s. " % self.active_movie
                        self.conversation_point = "processing"
                    else:
                        return partial_string + "OK, were you talking about %s? " % self.titles[self.dict[self.active_movie][0][-1]]
            if self.conversation_point == "confirming sentiment":
                new_sentiment = self.extract_sentiment(line)
                if new_sentiment == 0:
                    return partial_string + "I still can't tell what you thought about %s ." % self.active_movie
                else:
                    self.dict[self.active_movie][1] = new_sentiment
                    self.conversation_point = "processing"
            if self.conversation_point == "processing":
                for movie in self.active_movies_titles:
                    self.active_movie = movie
                    # Didn't find any movies of that name
                    if not self.dict[movie][0]:
                        self.dict[movie][0] = self.find_movies_closest_to_title(movie, 4)
                        if self.dict[movie][0]:
                            self.conversation_point = "confirming name"
                            return partial_string + "Did you mean %s? " % self.titles[self.dict[movie][0][-1]]
                        else:
                            self.dict.remove(movie)
                            partial_string += "I can't figure out what you were talking about when you say %s. " \
                                             "I'm going to move on, and if you can think of another name for " \
                                             "that movie, lmk. " % movie
                    # Found more than one movie by that name
                    if len(self.dict[movie][0]) > 1:
                        self.conversation_point = "confirming name"
                        return partial_string + "Did you mean %s? " % self.titles[self.dict[movie][0][-1]]
                    # Already talked about this movie
                    if self.dict[movie][0][0] in self.current_ratings:
                        self.conversation_point = "collecting"
                        return partial_string + "You've already told me about %s. " \
                                                "Let's talk about a different movie you've seen. " % self.titles(self.dict[movie][0][0])
                    # No sentiment detected
                    if self.dict[movie][1] == 0:
                        self.conversation_point = "confirming sentiment"
                        return partial_string + "Wait, what did you think about %s?" % movie
                    if self.dict[movie][1] > 1:
                        partial_string += ("Confirming that you loved %s. " % movie)
                    elif self.dict[movie][1] < 1:
                        partial_string += ("Confirming that you hated %s. " % movie)
                    elif self.dict[movie][1] > 0:
                        partial_string += ("Confirming that you liked %s. " % movie)
                    elif self.dict[movie][1] < 0:
                        partial_string += ("Confirming that you didn't like %s. " % movie)
                    self.ratings_given += 1
                    self.current_ratings[self.dict[movie][0][0]] = self.dict[movie][1]
                    self.active_movie = self.dict[movie][0][0]
                if self.ratings_given >= self.k:
                    self.conversation_point = "switchpoint"
                    return partial_string + "Do you want to tell me about another movie or switch to getting recommendations?"
                else:
                    self.conversation_point = "collecting"
                    return partial_string

        else:
          # already given enough information (after going through this loop at least 5 times)
          if self.ratings_given >= 5:
              # none left to recommend (based on k)
              if not self.top_movies:
                return "I'm sorry, those are all of my recommendations at the moment. Feel free to end our conversation with :quit and start a fresh conversation."
            # positive response detected
              elif line.lower() in self.pos_response:
                return "I never thought you'd ask! This movie might be even more perfect for you: \"%s\". Do you want another recommendation?" % self.top_movies.pop(0)[0]
            # negative response detected
              elif line.lower() in self.neg_response:
                return "No worries. Type :quit to exit and come back when you're ready for more recommendations. Enjoy the movie-watching!"
          # extract titles from user input
          movies = self.extract_titles(line)
          # ensure movie was captured
          if not movies:
            return "I'm sorry, I didn't catch that. Please put movie names inside quotation marks to help my understanding."
          elif len(movies) > 1:
            return "I'm sorry, I can only understand one movie at a time in starter mode."
          # find movie in archives
          movie_finder = self.find_movies_by_title(movies[0])
          if not movie_finder:
            return "I couldn't find any movies called \"%s\". I must admit that I'm extremely sensitive to spelling. Could you double check your title and try again?" % movies[0]
          if len(movie_finder) > 1:
            return "I know more than one movie named \"%s\". Can you clarify the year and title as follows: \"TITLE (YEAR)\"?" % movies[0]
          # capture sentiment for the user's sentence
          user_sentiment = self.extract_sentiment(line)
          if user_sentiment == 0:
            return "I couldn't detect if you enjoyed \"%s\" or not. Please tell me more about your feelings toward the movie." % movies[0]
          # update number of ratings given
          self.ratings_given += 1
          # populate current ratings vector for the user
          self.current_ratings[movie_finder[0]] = user_sentiment
          # not enough ratings given yet, prompt the user for more entries
          if self.ratings_given < 5:
            if user_sentiment == 1:
                return "I'm glad you liked \"%s\"! That movie is fantastic. Can you tell me about another movie you've seen?" % movies[0]
            elif user_sentiment == -1:
                return "I'm sorry you didn't like \"%s\". Perhaps you can tell me about another movie?" % movies[0]
          # compute recommendation, enough ratings given!
          if self.ratings_given == 5:
            # get indices from recommend function

            indices_recommended = self.recommend(self.current_ratings, self.ratings, self.k, self.creative)
            # get titles based on indices
            self.top_movies = [self.titles[x] for x in indices_recommended]
            # give user top recommendation
            if user_sentiment == 1:
                return "I'm glad you enjoyed \"%s\"! Based on your past movie experiences, I think you would like \"%s\". Would you like another recommendation?" % (movies[0], self.top_movies.pop(0)[0])
            elif user_sentiment == -1:
                return "I'm sorry you weren't a fan of \"%s\". However, I think you would enjoy \"%s\"! Would you like another recommendation?" % (movies[0], self.top_movies.pop(0)[0])
        return response

    def extract_titles(self, text):
      """Extract potential movie titles from a line of text.

      Given an input text, this method should return a list of movie titles
      that are potentially in the text.

      - If there are no movie titles in the text, return an empty list.
      - If there is exactly one movie title in the text, return a list
      containing just that one movie title.
      - If there are multiple movie titles in the text, return a list
      of all movie titles you've extracted from the text.

      Example:
        potential_titles = chatbot.extract_titles('I liked "The Notebook" a lot.')
        print(potential_titles) // prints ["The Notebook"]

      :param text: a user-supplied line of text that may contain movie titles
      :returns: list of movie titles that are potentially in the text
      """
      movie_titles = []
      
      # search for strings within quotation marks
      movie_regex = r"\"([^\"]+)\""
      movie_titles = re.findall(movie_regex, text)

      # TODO: creative part: very tricky, easy to have false positive
      # leave to the last, only trigger it when no titles found above???
      if self.creative and (not movie_titles):
        captialized_titles = re.findall(r"((?:[thean]{1,3}\s)?(?:[A-Z]\w+\s)*(?:[thean]{1,3}\s)?[A-Z]\w+)", text)
        movie_titles += captialized_titles
        no_quotation_titles = re.findall(r"(?:thought|think) (.*) was (?:great|good|amazing|terrible|best|awful|worst)", text)
        filtered_no_quotation_titles = []
        for each in no_quotation_titles:
          if each.lower() not in set(['this', 'that', 'it']):
            filtered_no_quotation_titles.append(each)
        movie_titles += filtered_no_quotation_titles
      return movie_titles


    def find_movies_by_title(self, title):
        """ Given a movie title, return a list of indices of matching movies.

        - If no movies are found that match the given title, return an empty list.
        - If multiple movies are found that match the given title, return a list
        containing all of the indices of these matching movies.
        - If exactly one movie is found that matches the given title, return a list
        that contains the index of that matching movie.

        Example:
          ids = chatbot.find_movies_by_title('Titanic')
          print(ids) // prints [1359, 1953]

        :param title: a string containing a movie title
        :returns: a list of indices of matching movies
        """
        # initialize matches and title list
        movie_match = []
        title = title.lower()
        titles = [title]
        tokens = title.split()
        if self.creative:
            articles = {"an", "a", "the",
                        'ein', 'eine', 'einer',
                        'eines', 'einem', 'einen',
                        'la', 'le', 'en', 'et', 'les', 'el', 'il',
                        'un', 'une', 'des', 'da', 'der', 'das',
                        'una', 'unos', 'unas',
                        'um', 'uma', 'uns', 'umas'}
        else:
            articles = {"an", "a", "the"}  # FIX: and -> a
        # take care of articles found
        if tokens[0].lower() in articles:
            new_title = ""
            if tokens[-1][0] != "(":
                new_title = " ".join(tokens[1:])
                new_title += ", " + tokens[0]
            # process parentheses
            else:
                new_title = " ".join(tokens[1:-1])
                new_title += ", " + tokens[0]
                new_title += " " + tokens[-1]
            titles.append(new_title)
        # print(titles)
        for i, movie in enumerate(self.titles):
            movie_name = movie[0].lower()
            trunc_movie_name = movie_name[:movie_name.find("(")].strip()
            movie_alias = re.findall(r"\((.*)\) \(", movie_name)  # alter/foreign titles
            regex = r"" + re.escape(title) + r"[^a-zA-Z$]"
            for title in titles:
                foundTitle = False
                # strip parentheses if needed, find match between movies in database
                if title == trunc_movie_name:
                    movie_match.append(i)
                    foundTitle = True
                elif title == movie_name:
                    movie_match.append(i)
                    foundTitle = True
                elif movie_alias and self.creative:  # alter/foreign titles
                    for alias in movie_alias:
                        alias = re.sub(r"a\.?k\.?a\.?", ' ', alias)
                        alias = alias.strip()
                        if alias == title:
                            movie_match.append(i)
                            foundTitle = True
                if self.creative and (not foundTitle) and re.search(regex, movie_name):  # disambiguation
                    # print(title, movie_name)
                    movie_match.append(i)
        return list(set(movie_match))

    def extract_sentiment(self, text):
        """Extract a sentiment rating from a line of text.

        You should return -1 if the sentiment of the text is negative, 0 if the
        sentiment of the text is neutral (no sentiment detected), or +1 if the
        sentiment of the text is positive.

        As an optional creative extension, return -2 if the sentiment of the text
        is super negative and +2 if the sentiment of the text is super positive.

        Example:
          sentiment = chatbot.extract_sentiment('I liked "The Titanic"')
          print(sentiment) // prints 1

        :param text: a user-supplied line of text
        :returns: a numerical value for the sentiment of the text
        """
        # initialize scores
        sent_score = 0
        super_sauce = 0
        # get rid of titles (don't want title to affect sentiment)
        titles = self.extract_titles(text)
        text_updated = text
        for t in titles:
            text_updated = text.replace(t, '')
        # get rid of punctuation
        text_updated_two = re.sub('[%s]' % re.escape(string.punctuation), '', text_updated)
        # break text into individual words
        text_updated_three = text_updated_two.split()

        # initialize temporary variables in loop
        neg_next = 1
        score = 0
        # print(text_updated_three)
        for i, word in enumerate(text_updated_three):

            # stemming
            # stem_word = self.stemmer.stem(word, 0,len(word)-1)

            # negation word classified as negative sentiment (find all words ending in nt if not in our list)
            if word in self.opposite or re.search("nt$", word):  # or stem_word in self.opposite
                neg_next *= -1
                if i == len(text_updated_three) - 1:
                    sent_score *= neg_next
                continue
            if self.creative:
                if word in self.strong_words:
                    # add weight if strong "super" word is present (2 or -2 returned)
                    super_sauce = 1
            if word in self.sentiment:
                # positive sentiment detected
                if self.sentiment[word] == 'pos':
                    score = 1
                # negative sentiment detected
                elif self.sentiment[word] == 'neg':
                    score = -1
                # flip score for next word if negation present
                score *= neg_next
                # reset negation variable
                neg_next = 1
                # compute running sentiment score
                sent_score += score
                # break out of loop if successful (to avoid double counting if present tense verb also there)
                continue
            # get entire word besides last letter if it is 'd'
            if word[-1:] == 'd':
                present_tense_word = word[0:-1]
                if present_tense_word in self.sentiment:
                    # support for past tense verbs such as 'loved' and 'liked'
                    if self.sentiment[present_tense_word] == 'pos':
                        score = 1
                    # support for past tense verbs such as 'hated' and 'disliked'
                    if self.sentiment[present_tense_word] == 'neg':
                        score = -1
                    score *= neg_next
                    neg_next = 1
                    sent_score += score
                    continue
            if word[-2:] == 'ed':
                present_tense_ed_word = word[0:-2]
                if present_tense_ed_word in self.sentiment:
                    # support for past tense verbs such as 'enjoyed'
                    if self.sentiment[present_tense_ed_word] == 'pos':
                        score = 1
                    # futher support for past tense verbs ending in 'ed'
                    if self.sentiment[present_tense_ed_word] == 'neg':
                        score = -1
                    score *= neg_next
                    neg_next = 1
                    sent_score += score

        # super sauce is 0 unless super negative or positive sentiment is detected in creative mode
        if sent_score > 0:
            sent_score = 1 + super_sauce
        elif sent_score < 0:
            sent_score = -1 - super_sauce

        return sent_score

    def extract_sentiment_for_movies(self, text):
        """Creative Feature: Extracts the sentiments from a line of text
        that may contain multiple movies. Note that the sentiments toward
        the movies may be different.

        You should use the same sentiment values as extract_sentiment, described above.
        Hint: feel free to call previously defined functions to implement this.

        Example:
          sentiments = chatbot.extract_sentiment_for_text('I liked both "Titanic (1997)" and "Ex Machina".')
          print(sentiments) // prints [("Titanic (1997)", 1), ("Ex Machina", 1)]

        :param text: a user-supplied line of text
        :returns: a list of tuples, where the first item in the tuple is a movie title,
          and the second is the sentiment in the text toward that movie
        """
        # TODO
        res = []
        titles = self.extract_titles(text)
        text_list = text.split()

        def classify_sentiment(sentiment):
            if sentiment > 0:
                sentiment = 1
            elif sentiment < 0:
                sentiment = -1
            else:
                sentiment = 0
            return sentiment

        if len(titles) == 0 and re.search(r"(it|that movie|that film)", text):
            sentiment = self.extract_sentiment(text)
            sentiment = classify_sentiment(sentiment)
            if self.active_movie:
                res.append((self.active_movie, sentiment))
        elif len(titles) == 1 or re.search(r"(both|and)", text):
            sentiment = self.extract_sentiment(text)
            sentiment = classify_sentiment(sentiment)
            for title in titles:
                res.append((title, sentiment))
        else:
            prevIdx, currIdx = 0, 0
            for title in titles:
                currIdx = text.find(title) + len(title) + 1
                sub_text = text[:currIdx]
                sentiment = self.extract_sentiment(sub_text)
                sentiment = classify_sentiment(sentiment)
                prevIdx = currIdx
                res.append((title, sentiment))
        return res

    def find_movies_closest_to_title(self, title, max_distance=3):
      """Creative Feature: Given a potentially misspelled movie title,
      return a list of the movies in the dataset whose titles have the least edit distance
      from the provided title, and with edit distance at most max_distance.

      - If no movies have titles within max_distance of the provided title, return an empty list.
      - Otherwise, if there's a movie closer in edit distance to the given title 
        than all other movies, return a 1-element list containing its index.
      - If there is a tie for closest movie, return a list with the indices of all movies
        tying for minimum edit distance to the given movie.

      Example:
        chatbot.find_movies_closest_to_title("Sleeping Beaty") # should return [1656]

      :param title: a potentially misspelled title
      :param max_distance: the maximum edit distance to search for
      :returns: a list of movie indices with titles closest to the given title and within edit distance max_distance
      """
      # TODO
      movie_match = []
      titles = [title]
      tokens = title.split()
      articles = {"an", "a", "the"} #FIX: and -> a
      # take care of articles found
      if tokens[0].lower() in articles:
        new_title = ""
        if tokens[-1][0] != "(":
          new_title = " ".join(tokens[1:])
          new_title += ", " + tokens[0]
        # process parentheses
        else:
          new_title = " ".join(tokens[1:-1])
          new_title += ", " + tokens[0]
          new_title += " " + tokens[-1]
        titles.append(new_title)

      closest_dist = max_distance
      names = []
      for i, movie in enumerate(self.titles):
          for title in titles:
              # strip parentheses if needed, find match between movies in database
              if movie[0].find("("):
                trunc_movie_name = movie[0][:movie[0].find("(")].strip()
              else:
                trunc_movie_name = movie[0]
              dist = self.findMinEditDistance(title, trunc_movie_name)
              if dist < closest_dist:
                movie_match = [i]
                closest_dist = dist
                names = [(title, trunc_movie_name, dist)]
              elif dist == closest_dist:
                movie_match.append(i)
                names.append((title, trunc_movie_name, dist))
      # print(names)
      return movie_match

  
    def findMinEditDistance(self, s, t):
      """
      Find the Levenshtein Distance between two strings s, t
      """

      rows = len(s)+1
      cols = len(t)+1
      deletion, insertion, substitution = 1, 1, 2
      
      dist = [[0 for _ in range(cols)] for _ in range(rows)]

      for row in range(1, rows):
          dist[row][0] = row * deletion

      for col in range(1, cols):
          dist[0][col] = col * insertion
          
      for col in range(1, cols):
          for row in range(1, rows):
            cost = 0 if s[row-1].lower() == t[col-1].lower() else substitution

            dist[row][col] = min(dist[row-1][col] + deletion, dist[row][col-1] + insertion, dist[row-1][col-1] + cost)
      
      return dist[row][col]


    def disambiguate(self, clarification, candidates):
      """Creative Feature: Given a list of movies that the user could be talking about 
      (represented as indices), and a string given by the user as clarification 
      (eg. in response to your bot saying "Which movie did you mean: Titanic (1953) 
      or Titanic (1997)?"), use the clarification to narrow down the list and return 
      a smaller list of candidates (hopefully just 1!)

      - If the clarification uniquely identifies one of the movies, this should return a 1-element
      list with the index of that movie.
      - If it's unclear which movie the user means by the clarification, it should return a list
      with the indices it could be referring to (to continue the disambiguation dialogue).

      Example:
        chatbot.disambiguate("1997", [1359, 2716]) should return [1359]
      
      :param clarification: user input intended to disambiguate between the given movies
      :param candidates: a list of movie indices
      :returns: a list of indices corresponding to the movies identified by the clarification
      """
      response = []
      # splits clarification
      clarify_length = len(clarification.split(" "))
      # loop over all candidates
      for candidate in candidates:
          # get title and split by spaces
          title = self.titles[candidate][0]
          title_toks = title.split(" ")
          if clarify_length < len(title_toks):
              for i in range(len(title_toks) - clarify_length + 1):
                  clar = "".join(clarification.split(" "))
                  # clarification found in titles
                  if clar == "".join(title_toks[i:i + clarify_length]) or "("+clar+")" == "".join(title_toks[i:i + clarify_length]):
                      response.append(candidate)
      
      return response

    #############################################################################
    # 3. Movie Recommendation helper functions                                  #
    #############################################################################

    def binarize(self, ratings, threshold=2.5):
      """Return a binarized version of the given matrix.

      To binarize a matrix, replace all entries above the threshold with 1.
      and replace all entries at or below the threshold with a -1.

      Entries whose values are 0 represent null values and should remain at 0.

      :param x: a (num_movies x num_users) matrix of user ratings, from 0.5 to 5.0
      :param threshold: Numerical rating above which ratings are considered positive

      :returns: a binarized version of the movie-rating matrix
      """
      #############################################################################
      # TODO: Binarize the supplied ratings matrix.                               #
      #############################################################################
      # The starter code returns a new matrix shaped like ratings but full of zeros.
      binarized_ratings = np.zeros_like(ratings)

      '''
      # code too slow for gradescope check!!!!
      for i, user_rate in enumerate(ratings):
          for j, movie_rate in enumerate(user_rate):
              if movie_rate > threshold: # positive rating
                  binarized_ratings[i][j] = 1
              elif movie_rate == 0: # null values
                  binarized_ratings[i][j] = 0
              elif movie_rate <= threshold: # negative rating
                  binarized_ratings[i][j] = -1
      '''

      ratings[ratings == 0] = 100 # value larger than 5 to get above threshold
      ratings[ratings <= threshold] = -1
      ratings[ratings == 100] = 0 # back to 0 value after less than threshold test
      ratings[ratings > threshold] = 1
      
      #############################################################################
      #                             END OF YOUR CODE                              #
      #############################################################################
      return ratings


    def similarity(self, u, v):
      """Calculate the cosine similarity between two vectors.

      You may assume that the two arguments have the same shape.

      :param u: one vector, as a 1D numpy array
      :param v: another vector, as a 1D numpy array

      :returns: the cosine similarity between the two vectors
      """
      #############################################################################
      # TODO: Compute cosine similarity between the two vectors.
      #############################################################################
      # make sure u and v are numpy arrays
      param_one = np.array(u)
      param_two = np.array(v)
      # avoid division by 0 (causes chatbot to give runtime warnings if omitted)
      if (np.linalg.norm(param_one) == 0 or np.linalg.norm(param_two) == 0):
          return 0
      # calculate cosine similarity
      similarity = np.dot(param_one, param_two) / (np.linalg.norm(param_one) * np.linalg.norm(param_two))
      #############################################################################
      #                             END OF YOUR CODE                              #
      #############################################################################
      return similarity


    def recommend(self, user_ratings, ratings_matrix, k=10, creative=False):
      """Generate a list of indices of movies to recommend using collaborative filtering.

      You should return a collection of `k` indices of movies recommendations.

      As a precondition, user_ratings and ratings_matrix are both binarized.

      Remember to exclude movies the user has already rated!

      :param user_ratings: a binarized 1D numpy array of the user's movie ratings
      :param ratings_matrix: a binarized 2D numpy matrix of all ratings, where
        `ratings_matrix[i, j]` is the rating for movie i by user j
      :param k: the number of recommendations to generate
      :param creative: whether the chatbot is in creative mode

      :returns: a list of k movie indices corresponding to movies in ratings_matrix,
        in descending order of recommendation
      """

      #######################################################################################
      # TODO: Implement a recommendation function that takes a vector user_ratings          #
      # and matrix ratings_matrix and outputs a list of movies recommended by the chatbot.  #
      #                                                                                     #
      # For starter mode, you should use item-item collaborative filtering                  #
      # with cosine similarity, no mean-centering, and no normalization of scores.          #
      #######################################################################################
      # Populate this list with k movie indices to recommend to the user.
      recommendations = []
      movie_rating_set = []

      for i, rating in enumerate(user_ratings):
          # user did not rate the movie already
          if rating == 0:
              cos_sim = np.zeros(len(user_ratings))
              for j, rating_by_all in enumerate(ratings_matrix):
                  if user_ratings[j] != 0:
                      item_item_sim = self.similarity(ratings_matrix[i], rating_by_all)
                      cos_sim[j] = item_item_sim
              user_score = np.dot(cos_sim, user_ratings)
              movie_rating_set.append((i, user_score))

      sorted_scores = sorted(movie_rating_set, key=lambda tup:tup[1], reverse=True)

      for i in range(0, k):
          if sorted_scores[i][0] > 0:
            recommendations.append(sorted_scores[i][0])
      #############################################################################
      #                             END OF YOUR CODE                              #
      #############################################################################
      return recommendations


    #############################################################################
    # 4. Debug info                                                             #
    #############################################################################

    def debug(self, line):
      """Return debug information as a string for the line string from the REPL"""
      # Pass the debug information that you may think is important for your
      # evaluators
      debug_info = 'debug info'
      return debug_info


    #############################################################################
    # 5. Write a description for your chatbot here!                             #
    #############################################################################
    def intro(self):
      """Return a string to use as your chatbot's description for the user.

      Consider adding to this description any information about what your chatbot
      can do and how the user can interact with it.
      """
      return """
      Hi, I'm MovieMaster, the movie recommendation chatbot. Tell me your feelings about past movies you've seen, and I will recommend new movies based on your preferences!
      """


if __name__ == '__main__':
  print('To run your chatbot in an interactive loop from the command line, run:')
  print('    python3 repl.py')
