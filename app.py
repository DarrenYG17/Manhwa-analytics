from WebScraper import WebScraper as WebScraperClass
from ReviewAnalysis import ReviewAnalysis as ReviewAnalysisClass
import json
import streamlit as st
from rapidfuzz import fuzz
from wordcloud import WordCloud
import matplotlib.pyplot as plt

class Application:
    
    def __init__(self, fileName):
        self.aliasLinkDict = None
        self.nameArrays = None
        self.loadAliasDict(fileName)

        st.title("Manhwa analytics application")
        st.write("Analyze and visualize data relating to manhwas easily.")
        self.run()

    #streamlit section
    def run(self):
        if "matchingNameList" not in st.session_state:
            st.session_state.matchingNameList = []
        
        col1, col2 = st.columns([3, 1]) 
        with col1:
            manhwaTitle = st.text_input("Enter a manhwa title:", label_visibility="collapsed", placeholder="Search manhwa...").strip()
        with col2:
            fetchClicked = st.button("🔍 Fetch")

        if fetchClicked:
            if not manhwaTitle:
                st.write("⚠️Input a manhwa title⚠️")
            elif len(manhwaTitle) < 2:
                st.write("⚠️Input must be more than 1 letter⚠️")
            else:
                st.session_state.matchingNameList = self.findMatchingName(manhwaTitle)
        
        if st.session_state.matchingNameList:
            if len(st.session_state.matchingNameList) == 1:
                self.displayResultForChoice(st.session_state.matchingNameList[0].lower())
            else:
                limited = st.session_state.matchingNameList[:10]
                limited = ["Select from suggested..."] + limited
                choice = st.selectbox("Matching results:", limited).lower()
                if choice != "select from suggested...":
                    self.displayResultForChoice(choice)
    
    def displayResultForChoice(self, choice):
        details = self.getDetailsOfManhwa(choice)
        reviewAnalysis = self.getReviewAnalysisOfManhwa(choice)
        st.write(details)
        st.write(reviewAnalysis)
        st.pyplot(self.generateWordCloud(reviewAnalysis))

    #application section
    def generateWordCloud(self, data):
        freqs = {kw["phrase"].replace(" ", "_"): kw["count"] for kw in data["keywords"]}
        wc = WordCloud(width=800, height=400, background_color="white").generate_from_frequencies(freqs)

        # display
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")

        return fig
            
    def findMatchingName(self, string):
        search = string.lower()
        matching = []
        for i in self.nameArrays:
            highestMatchRatio = 0
            for j in i:
                ratio = fuzz.partial_ratio(search, j)
                if ratio > 75 and ratio > highestMatchRatio:
                    highestMatchRatio = ratio
            if int(highestMatchRatio) != 0:
                matching.append([highestMatchRatio, i[0]])
            elif int(highestMatchRatio) == 100:
                return [i[0]]
        
        matching.sort(key=lambda x: x[0], reverse=True)
        matchingNames = [x[1].title() for x in matching]
        return matchingNames

    
    def loadAliasDict(self, fileName):
        alias = {}
        nameArrays = []
        with open(fileName, "r", encoding="utf-8") as f:
            for line in f:
                entry = json.loads(line)
                link = entry["link"]
                nameArrays.append(entry["names"])
                for i in entry["names"]:
                    alias[i] = link
        self.aliasLinkDict = alias
        self.nameArrays = nameArrays

    def searchForLinkByManhwa(self, string):
        return self.aliasLinkDict.get(string)
    
    def getDetailsOfManhwa(self, string):
        link = self.searchForLinkByManhwa(string)
        if link:
            return WebScraperClass.getDetails(link)
        else:
            return(f'\"{string}\" doesnt exist in collected data, couldnt fetch details')

    def getReviewAnalysisOfManhwa(self, string):
        link = self.searchForLinkByManhwa(string)
        if link:
            reviews = WebScraperClass.getReviews(link)
            analysis = ReviewAnalysisClass.analyseReviews(reviews)
            return analysis
        else:
            return(f'\"{string}\" doesnt exist in collected data, couldnt fetch review analysis')
    

if __name__ == "__main__":
    app = Application("alias.jsonl")