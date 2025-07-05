import news
import politics

companies=["Microsoft", "Nvidia", "Apple", "Amazon", "Alphabet", "Tesla"]

news_extractor=news.NewsExtractor()
political_analizer=politics.PoliticalUncertaintyAnalyzer(use_llm=True)
batch_results={}
news_per_company={}

for company in companies:
    queries_per_company=political_analizer.political_queries[company]["queries"]
    news_per_company[company]=[]
    for query in queries_per_company:
        news_per_company[company].append( news_extractor.search_news_google(query,1))

for company in news_per_company.keys():
    batch_results[company] = political_analizer.enhanced_political_analysis(news_per_company[company],company )
print(batch_results)
    
   
   




# enhanced_result = political_analizer.enhanced_political_analysis(j,company )
# batch_results[company] = enhanced_result
#print(batch_results)
 # def get_news_data1(self):
    #     start=time.time()
    #     news_per_company={}
    #     #inisilize the news_per_company dict
    #     for company in self.political_queries.keys():
    #         news_per_company[company]=[]

    #     for company in self.political_queries.keys():
    #         queries=self.political_queries[company]
    #         #making a new method in news extractor for varius topic
    #         news=self.news_extractor.search_gnews_lits_of_topics(queries,3)
    #         #add each news in news_per_company[company]
    #         for n in news:    
    #             news_per_company[company].append(n)
       
    #     end=time.time()
    #     print('duration',end-start)
    #     return news_per_company
    

