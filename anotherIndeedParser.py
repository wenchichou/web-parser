# Parse indeed.com
# modified scripts from 
# 1) http://blog.nycdatascience.com/student-works/project-3-web-scraping-company-data-from-indeed-com-and-dice-com/
# 2) https://jessesw.com/Data-Science-Skills/
# load the library
from bs4 import BeautifulSoup # For HTML parsing
import urllib2 # Website connections
import re # Regular expressions
from time import sleep # To prevent overwhelming the server between connections
from collections import Counter # Keep track of our term counts
from nltk.corpus import stopwords # Filter out stopwords, such as 'the', 'or', 'and'
import pandas as pd # For converting results to a dataframe and bar chart plots
#%pylab inline
import requests
from pprint import pprint
import sys


def text_cleaner(website):
    '''
    This function just cleans up the raw html so that I can look at it.
    Inputs: a URL to investigate
    Outputs: Cleaned text only
    '''
    try:
        site = urllib2.urlopen(website).read() # Connect to the job posting
    except: 
        return   # Need this in case the website isn't there anymore or some other weird connection problem 

    soup_obj = BeautifulSoup(site, "html.parser") # Get the html from the site

    for script in soup_obj(["script", "style"]):
        script.extract() # Remove these two elements from the BS4 object

    text = soup_obj.get_text() # Get the text from this

    rawLines = (line.strip() for line in text.splitlines()) # break into lines
    #print '\n'.join(lines)
    print website
    
    #lines = rawLines
    # extract the lines having words more than 10
    lines = [s for s in rawLines if len(s.split()) >= 10 ]
#    for line in lines:
#        print "wordCount:",len(line.split())
#        print line
    

    # chunks = (phrase.strip() for line in lines for phrase in line.split("  ")) # break multi-headlines into a line each

    # def chunk_space(chunk):
    #     chunk_out = chunk + ' ' # Need to fix spacing issue
    #     return chunk_out  

    # text = ''.join(chunk_space(chunk) for chunk in chunks if chunk).encode('utf-8') # Get rid of all blank lines and ends of line

    # # Now clean out all of the unicode junk (this line works great!!!)
    # try:
    #     text = text.decode('unicode_escape').encode('ascii', 'ignore') # Need this as some websites aren't formatted
    # except:                                                            # in a way that this works, can occasionally throw
    #     return                                                         # an exception

    # text = re.sub("[^a-zA-Z.+3]"," ", text)  # Now get rid of any terms that aren't words (include 3 for d3.js)
    #                                             # Also include + for C++

    # text = text.lower().split()  # Go to lower case and split them apart

    # stop_words = set(stopwords.words("english")) # Filter out any stop words
    # text = [w for w in text if not w in stop_words]

    # text = list(set(text)) # Last, just get the set of these. Ignore counts (we are just looking at whether a term existed
    #                         # or not on the website)
    # return text
    return '; '.join(lines)

# indeed.com url
#base_url = 'http://www.indeed.com/jobs?q=bioinformatics+research+assistant&l=Cambridge+MA&jt=fulltime&sort='
city_title = 'MA'
job_keywords = 'bioinformatics+manage'
base_url = 'http://www.indeed.com/jobs?q=%s&l=%s&sort=' % (job_keywords, city_title)
sort_by = 'date'          # sort by data
start_from = '&start='    # start page number

pd.set_option('max_colwidth',500)    # to remove column limit (Otherwise, we'll lose some info)
df = pd.DataFrame()   # create a new data frame

#url ="http://www.indeed.com/jobs?q=bioinformatics&l=MA&jt=fulltime&sort=date&start=0"
#f = urllib2.urlopen(url).read()
#target = Soup(f)
#targetElements = target('div',attrs={'class': 'row'})
#elem = targetElements[0]
#comp_name = elem.find('span', attrs={'itemprop':'name'}).getText().strip()

url = "%s%s" % (base_url, sort_by)
print(url)
html = urllib2.urlopen(url).read()
soup = BeautifulSoup(html, "html.parser")

num_jobs_area = soup.find(id = 'searchCount').string.encode('utf-8') # Now extract the total number of jobs found # The 'searchCount' object has this
job_numbers = re.findall('\d+', num_jobs_area) # Extract the total jobs found from the search result

if len(job_numbers) > 3: # Have a total number of jobs greater than 1000
    total_num_jobs = (int(job_numbers[2])*1000) + int(job_numbers[3])
else:
    total_num_jobs = int(job_numbers[2]) 

print 'There were', total_num_jobs, 'jobs found in', city_title # Display how many jobs were found

num_pages = total_num_jobs/10 # This will be how we know the number of times we need to iterate over each new
                                      # search result page

#for page in range(1,num_pages+1): # page from 1 to 100 (last page we can scrape is 100)
for page in range(1,2): # page from 1 to 100 (last page we can scrape is 100)
    page = (page-1) * 10
    url = "%s%s%s%d" % (base_url, sort_by, start_from, page) # get full url
    f = urllib2.urlopen(url).read()
    target = BeautifulSoup(f, "html.parser")
    #target = Soup(urllib.urlopen(url), "lxml")
    #targetElements = target.findAll('div', attrs={'class' : '  row  result'}) # we're interested in each row (= each job)
    targetElements = target('div',attrs={'class': 'row'})
    # trying to get each specific job information (such as company name, job title, urls, ...)
    for elem in targetElements:
        #comp_name = elem.find('span', attrs={'itemprop':'name'}).getText().strip()
        if elem.find('span', attrs={'class':'company'}):
            comp_name = elem.find('span', attrs={'class':'company'}).getText().encode('utf-8').strip()
            #print(comp_name)
        if elem.find('a', attrs={'class':'turnstileLink'}):
            job_title = elem.find('a', attrs={'class':'turnstileLink'}).attrs['title'].encode('utf-8').strip()
            #print(job_title)
        home_url = "http://www.indeed.com"
        job_link = "%s%s" % (home_url,elem.find('a').get('href'))
        #print(job_link)
        if elem.find('span', attrs={'itemprop':'addressLocality'}):
            job_addr = elem.find('span', attrs={'itemprop':'addressLocality'}).getText()
            #print(job_addr)
        else: job_addr = ""
        job_posted = elem.find('span', attrs={'class': 'date'}).getText()
        if "days ago" in job_posted:
            job_posted = re.sub(' days ago', '', job_posted)
            job_posted = re.sub('\+', '', job_posted)
        else: job_posted = 0.5
        if elem.find('span', attrs={'itemprop':'name'}):
            comp_link_overall = elem.find('span', attrs={'itemprop':'name'}).find('a')
            if comp_link_overall != None:
                comp_link_overall = "%s%s" % (home_url, comp_link_overall.attrs['href'])
                #print(comp_link_overall)
            else: comp_link_overall = ""
        else: comp_link_overall = ""
#        if comp_link_overall != None: # if company link exists, access it. Otherwise, skip.
#            comp_link_overall = "%s%s" % (home_url, comp_link_overall.attrs['href'])
#        else: comp_link_overall = None
        identifier="%s @ %s" % (job_title,comp_name)
        df = df.append({'identifier': identifier, 'comp_name': comp_name, 'job_title': job_title,
                        'job_link': job_link, 'job_posted': job_posted,
                        'overall_link': comp_link_overall, 'job_location': job_addr,
                        'job_description' : None
                       }, ignore_index=True)

# get size of df
print(df.shape)
cols = ['job_posted','identifier','job_location','job_description','comp_name','job_title','job_link','overall_link']
df = df[cols]
df2 = df.drop_duplicates(subset='identifier', keep='last')
print(df2.shape)
df2 = df2.sort_values(by="job_posted")
#print(df['job_link'][0])
#df.to_csv("./Indeed.Bioinformatics.ResearchAssistant.results.csv")

for index, row in df2.iterrows():
    print row['identifier']
    row['job_description'] = text_cleaner(row['job_link'])
#sample = text_cleaner(df['job_link'][1])
#print(sample)

df2.to_csv("./test.results.csv", encoding='utf-8')



