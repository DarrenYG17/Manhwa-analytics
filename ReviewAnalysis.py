import pandas as pd
import string
#import pkg_resources
#from symspellpy import SymSpell, Verbosity
import emoji
from sentence_transformers import SentenceTransformer
import hdbscan
from collections import defaultdict
from keybert import KeyBERT
import json



class ReviewAnalysis:
    fileToWriteTo = "reviewAnalysis.jsonl"
    reviewFile = "manhwaReviews.jsonl"
    kbModel = KeyBERT("all-MiniLM-L6-v2")
    STmodel = SentenceTransformer("all-MiniLM-L6-v2")
    analysedLinkDict = {}

    @classmethod
    def getAnalysedLinks(cls):
        dict = {}
        df = pd.read_json(cls.fileToWriteTo, lines=True)
        for i in range(df.shape[0]):
            row = df.iloc[i]
            dict[row['link']] = {"noOfReviews": int(row["noOfReviews"]), "averageScore": float(row["averageScore"]), "keywords":row["keywords"]}
        return dict
    
    @classmethod
    def updateAnalysedLinkDict(cls):
        cls.analysedLinkDict = cls.getAnalysedLinks()

    @classmethod
    def analyseReviews(cls, reviews):
        print(f'analysing {reviews["link"]}')
        allReviews= reviews["reviews"] #currently very dependant on file structure
        if cls.analysedLinkDict.get(reviews["link"]):
            return {"link" :reviews["link"]} | cls.analysedLinkDict.get(reviews["link"])

        #number of reviews
        noOfReviews = len(allReviews)

        if noOfReviews:
            # calculate average score
            total = 0
            if len(allReviews) > 0:
                for j in allReviews:
                    total += int(j["score"])
                average = round(total / len(allReviews), 2)

            #cluster reviews
            clusterList = cls.clusterReviewPhrases(allReviews)
        else:
            average = 0
            clusterList =[]

        result = {"link": reviews['link'], "noOfReviews": noOfReviews, "averageScore": average, "keywords": clusterList}
        cls.writeToFile(result)
        return result
        
    @classmethod
    def clusterReviewPhrases(cls, reviewArray):
        #extract only the reviews content
        justReviews = []
        for i in reviewArray:
            justReviews.append(i["content"])
        
        #clean each one
        for i in range(len(justReviews)):
            justReviews[i] = cls.cleanReview(justReviews[i])
            
        #cluster
            #collect keywords
        kbModel = cls.kbModel
        allKeyWords = []
        for i in justReviews:
            keywords = kbModel.extract_keywords(i, keyphrase_ngram_range=(1, 4), stop_words='english', top_n=5)
            allKeyWords.extend(keyword[0] for keyword in keywords)

            #clustering
        model = cls.STmodel
        embeddings = model.encode(allKeyWords, convert_to_numpy=True, show_progress_bar=True)
        
        clusterer = hdbscan.HDBSCAN(min_cluster_size=3, metric='euclidean')
        labels = clusterer.fit_predict(embeddings)
        clusters = defaultdict(list)
        for phrase, label in zip(allKeyWords, labels):
            clusters[label].append(phrase)

        clusterArray = []
            #summarising clusters
        for label, phrases in clusters.items():
            numberOfPhrases = 0
            if label != -1:
                for i in phrases:
                    numberOfPhrases+=1
                thisCluster = {"phrase":phrases[1], "count":numberOfPhrases}
                clusterArray.append(thisCluster)

        return(clusterArray)

    @classmethod
    def cleanReview(cls, review):
        #remove punctuation
        translator = str.maketrans('', '', string.punctuation)
        noPuncText = review.translate(translator)
        
        #replace slang
            #find some online database on different slangs?

        #remove emojis
        noEmojiText = emoji.replace_emoji(noPuncText, replace='')

        #replace typos
        ''' takes too much time compared to how necessary it is
        sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
        dictionary_path = pkg_resources.resource_filename("symspellpy", "frequency_dictionary_en_82_765.txt")
        sym_spell.load_dictionary(dictionary_path, term_index=0, count_index=1)
        suggestions = sym_spell.lookup_compound(noEmojiText, max_edit_distance=2)
        typoCleanedText = suggestions[0].term if suggestions else noEmojiText

        return typoCleanedText.lower()
        '''
        
        return noEmojiText.lower()
    
    @classmethod
    def writeToFile(cls, result):
        with open(cls.fileToWriteTo, "a", encoding="utf-8") as file:
            json.dump(result, file, ensure_ascii=False)
            file.write("\n")
            file.flush()

    @classmethod
    def analyseReviewsFromFile(cls):
        with open(cls.reviewFile, "r", encoding="utf-8") as f:
            for line in f:
                entry = json.loads(line)
                cls.analyseReviews(entry)

ReviewAnalysis.updateAnalysedLinkDict()

if __name__ == "__main__":
    ReviewAnalysis.analyseReviewsFromFile()