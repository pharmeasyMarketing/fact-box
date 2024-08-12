import streamlit as st
import requests
import os
from bs4 import BeautifulSoup, Tag
import pandas as pd
import urllib.parse
from newspaper import Article
from bs4 import BeautifulSoup
import re
import openai
import random

import nltk
nltk.download('punkt_tab')

pd.set_option("display.max_colwidth", None)

def concate_query(keyword):
    return keyword + " Facts and statistics in Umited states"

def scrape_google(query, count=20):
    query_encoded = urllib.parse.quote(query)
    url = f"https://www.google.com/search?q={query_encoded}&num={count}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    headings = soup.find_all("h3")
    links = []

    for heading in headings:
        try:
            link = heading.find_previous("a")["href"]
        except (TypeError, KeyError):
            link = ""
        links.append(link)

    data = [(heading.get_text(), link) for heading, link in zip(headings, links)]
    # pd.set_option("display.max_colwidth", None)

    df = pd.DataFrame(data, columns=["Heading", "URL"])
    # filename = f"{query}_scrap_google_result.csv"
    # df.to_csv(filename, index=False)
    # print(f"scrap google result file saved as '{filename}' ")
    return df

def filtered_url(df):
    website_list = [
    "https://www.who.int/",
    "https://diabetes.org/",
    "https://www.kidney.org/",
    "https://www.heart.org/",
    "https://www.cancer.org/",
    "https://gastro.org/",
    "https://www.aao.org/",
    "who.int",
    "https://www.nin.res.in/",
    "https://www.aad.org/",
    "https://www.ianindia.org/",
    "https://www.psychiatry.org/",
    "https://www.indianrheumatology.org/",
    "https://www.lung.org/",
    "https://www.auajournals.org/",
    "https://www.cdc.gov/",
    "https://www.endocrine.org/",
    "https://www.brainfacts.org/",
    "https://www.rheumatology.org/",
    "https://www.nih.gov/",
    "https://pubmed.ncbi.nlm.nih.gov/",
    "https://medscape.com/",
    "https://www.nhm.gov.in/",
    "https://www.mohfw.gov.in/",
    "https://www.ncbi.nlm.nih.gov/",
    "https://main.icmr.nic.in/",
    "https://www.wma.net/",
    "https://www.nlm.nih.gov/",
    "https://www.ima-india.org/",
    "https://www.nice.org.uk/",
    "https://www.cochranelibrary.com/",
    "https://www.escardio.org/",
    "https://www.ersnet.org/",
    "https://www.ama-assn.org/",
    "https://www.thelancet.com/",
    "https://www.nejm.org/",
    "https://www.bmj.com/",
    "https://jamanetwork.com/",
    "https://www.sciencedirect.com/",
    "https://www.journal-surgery.net/",
    "https://www.plos.org/",
    "https://www.nhs.uk/",
    "https://hints.cancer.gov/",
    ".gov",
    "https://www.ahrq.gov/",
    "https://www.statista.com/"
    ]


    filtered_urls = set()
    for index, row in df.iterrows():
        url = row["URL"]
        for website in website_list:
            if website in url:
                filtered_urls.add(url)
                break

    df["Filtered Url"] = pd.Series(list(filtered_urls))
    return df

def scrape_article(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        return article.text
    except:
        return ""

def get_article(url):
    headers = {'User-Agent': random.choice(USER_AGENTS)}
    for _ in range(10):
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            text_content = soup.get_text()
            return text_content
    raise Exception('Error getting article: {}'.format(response.status_code))


USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36',
    'Mozilla/5.0 (Linux; Android 10; Pixel 3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Mobile Safari/537.36',
]

def pubmed_article_scrap(url):
    try:
        content = get_article(url)
        soup = BeautifulSoup(content, 'html.parser')
        text = [p.get_text() for p in soup.find_all('p')]
        text = '\n'.join(text)
        return text
    except:
        return ""




def count_tokens( list_of_article, topic, num_facts):

    prompt = f'''
    You are a specialized medical researcher or practitioner. A collection of articles titled '{list_of_article}' that delve into the subject matter of '{topic}' has been handed to you. Each article comes with the web page source from which the data has been procured. Your role involves conducting a detailed review and comprehension of these articles, discarding any superfluous information, and subsequently drawing out {num_facts} crisp facts to the provided topic. Each fact needs to be straightforward, and formatted under 15 words. These facts are to be organized in a numbered list with the accompanying source link for each fact, denoting the domain name of the source website.

    Guidelines:
    - Facts should be- only related to topic:{topic}. Please don't show any facts if it's not around the topic, but don't give the random facts
    - while creating or listing the facts give first priority to pubmed, ncbi and other .gov websites.
    - Never create any fact from outside the list, also, please avoide mentioning source randomly. Make sure sources should be taken from the shared list of artciles. not from anywhere. else.
    - Shorten and keep the points crisp and strictly under 15 words.
    - Get gacts from each list of article. not rely only on one or two source, for example, if 10 sources are present try to get facts from each sources. 
    - Facts should be stastics based and have numbers in it. 
    - The facts should be arranged in an ordered, numbered list.
    - Each fact should include the source in the format '[source: [domain_name](URL)]'. Replace 'domain_name' with the actual domain name from the list of articles, and 'URL' with the complete URL from the article list. The source should be hyperlinked with the anchor text representing the source name, never create new list to show source, only hyperlink them in the anchor text at the end of each facts, also please avoide mentioning source randomly. Make sure sources should be taken from the shared list of artciles not from anywhere else.
    - The source link should be with nofollow tag. Please follow this strictly. example: <li>Home pregnancy tests are about 97-99% accurate if instructions are followed carefully. <a href="https://www.cdc.gov/nchs/fastats/births.htm" target="_blank" rel="noreferrer noopener nofollow">source: CDC</a></li>, 
    '''
    tokens = nltk.word_tokenize(prompt)
    return len(tokens)
    

@st.cache_data(show_spinner=False)
def generate_facts(list_of_article, topic, num_facts, model="gpt-3.5-turbo-16k", max_tokens=2000, temperature=0.2):


# Create a separate copy of the list using slicing
    # copy_list = list_of_article[:]

    # word_count = 0
    # for sublist in copy_list:
    #     for string in sublist:
    #         words = string.split()
    #         word_count += len(words)

    # st.write(word_count)
    # st.write(list_of_article)
    token_count = count_tokens(list_of_article, topic, num_facts)
    
    if token_count > 9000:
        # st.write("inside first if")
       
        part_length = len(list_of_article) // 3
        list_of_article_part1 = list_of_article[:part_length]

        part_length = len(list_of_article) // 3
        list_of_article_part1 = list_of_article[:part_length]


        if count_tokens(list_of_article_part1, topic, num_facts) > 9000:
            url = list_of_article_part1[0][0]  
            article_text1 = "".join([element[1] for element in list_of_article_part1])  

            # st.write("inside list part 1")
            part_length1 = len(article_text1) // 3
            part1 = [url, article_text1[:part_length1]]
            part2 = [url, article_text1[part_length1: part_length1 * 2]]
            part3 = [url, article_text1[part_length1 * 2:]]

            
            response_part1 = generate_facts_helper(part1, topic, num_facts)
            response_part2 = generate_facts_helper(part2, topic, num_facts)
            response_part3 = generate_facts_helper(part3, topic, num_facts)

           
            response1 = response_part1 + response_part2 + response_part3
        else:
            response1 = generate_facts_helper(list_of_article_part1, topic, num_facts)

        # st.write(response1)

        # Check if token count of list_of_article_part2 exceeds 13000
        list_of_article_part2 = list_of_article[part_length: 2 * part_length]
        if count_tokens(list_of_article_part2, topic, num_facts) > 9000:

            # st.write("inside list part 2")
            url = list_of_article_part2[0][0]  # Extract URL from the first element of list_of_article_part2
            article_text2 = "".join([element[1] for element in list_of_article_part2])  # Concatenate article texts

            # Split article_text2 into three parts
            part_length2 = len(article_text2) // 3
            part4 = [url, article_text2[:part_length2]]
            part5 = [url, article_text2[part_length2: part_length2 * 2]]
            part6 = [url, article_text2[part_length2 * 2:]]

            # Generate facts for each part
            response_part4 = generate_facts_helper(part4, topic, num_facts)
            response_part5 = generate_facts_helper(part5, topic, num_facts)
            response_part6 = generate_facts_helper(part6, topic, num_facts)

            # Combine the responses
            response2 = response_part4 + response_part5 + response_part6
        else:
            response2 = generate_facts_helper(list_of_article_part2, topic, num_facts)

        # st.write(response2)

        # Check if token count of list_of_article_part3 exceeds 13000
        list_of_article_part3 = list_of_article[2 * part_length:]
        if count_tokens(list_of_article_part3, topic, num_facts) > 9000:

            # st.write("inside list part 3")
            url = list_of_article_part3[0][0]  # Extract URL from the first element of list_of_article_part3
            article_text3 = "".join([element[1] for element in list_of_article_part3])  # Concatenate article texts

            # Split article_text3 into three parts
            part_length3 = len(article_text3) // 3
            part7 = [url, article_text3[:part_length3]]
            part8 = [url, article_text3[part_length3: part_length3 * 2]]
            part9 = [url, article_text3[part_length3 * 2:]]

            # Generate facts for each part
            response_part7 = generate_facts_helper(part7, topic, num_facts)
            response_part8 = generate_facts_helper(part8, topic, num_facts)
            response_part9 = generate_facts_helper(part9, topic, num_facts)

            # Combine the responses
            response3 = response_part7 + response_part8 + response_part9
        else:
            response3 = generate_facts_helper(list_of_article_part3, topic, num_facts)

        # st.write(response3)

        total = response1 + response2 + response3
        # st.write(total)
        # st.write("final response")
        # st.write(type(response))
        # st.write(response)
        # st.write("filtered reponse")
        response = filter_response(total, topic, num_facts)

    else:
        # st.write("inside else")
        response = generate_facts_helper(list_of_article, topic, num_facts, model, max_tokens, temperature)
    
    return response



def filter_response(response_list, topic, num_facts, model="gpt-3.5-turbo-16k", max_tokens=1000, temperature=0.2):

    prompt = f'''We have a list of facts that require filtering. Your task is to randomly extract {num_facts} facts from the given list that are more suitable for the topic: "{topic}". Please adhere to the following guidelines:
    - Facts should be- only related to topic:{topic}. Please don't show any facts if it's not around the topic, but don't give the random facts
    - while creating or listing the facts give first priority to pubmed, ncbi and other .gov websites.
    - Preserve the original wording of the facts; do not rewrite them. Simply select and filter {num_facts} facts from the list.
    - While filtering, randomly choose facts that are relevant to the topic: "{topic}". Ensure that the facts come from different sources,rather than a single source, but it should not go against the given data if in given data multiple sources are not available then never add random sources by your own. You can identify the different sources by looking for the "source: [source name]" at the end of each fact.
    - Retain any links present in the facts. If possible, add the "nofollow" attribute to the links.
    Here is the fact list for reference: {response_list}.
   
]
    '''

    gpt_response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content":  prompt,
            },
            
        ],
        max_tokens=max_tokens,
        n=1,
        stop=None,
        temperature=temperature,
    )
    response = gpt_response["choices"][0]["message"]["content"].strip()
    response = response
    return response



@st.cache_data(show_spinner=False)
def generate_facts_helper(list_of_article, topic, num_facts, model="gpt-3.5-turbo-16k", max_tokens=2000, temperature=0.2):
    prompt = f'''
    You are a specialized medical researcher or practitioner. A collection of articles titled '{list_of_article}' that delve into the subject matter of '{topic}' has been handed to you. Each article comes with the web page source from which the data has been procured. Your role involves conducting a detailed review and comprehension of these articles, discarding any superfluous information, and subsequently drawing out {num_facts} crisp facts to the provided topic. Each fact needs to be straightforward, and formatted under 15 words. These facts are to be organized in a numbered list with the accompanying source link for each fact, denoting the domain name of the source website.

    Guidelines:
    - Facts should be- only related to topic:{topic}. Please don't show any facts if it's not around the topic, but don't give the random facts.
    - while creating or listing the facts give first priority to pubmed, ncbi and other .gov websites.
    - Shorten and keep the points crisp and strictly under 15 words.
    - Get gacts from each list of article. not rely only on one or two source, for example, if 10 sources are present try to get facts from each sources. 
    - Facts should be stastics based and have numbers in it. 
    - The facts should be arranged in an ordered, numbered list.
    - Each fact should include the source in the format '[source: [domain_name](URL)]'. Replace 'domain_name' with the actual domain name from the list of articles, and 'URL' with the complete URL from the article list. The source should be hyperlinked with the anchor text representing the source name, never create new list to show source, only hyperlink them in the anchor text at the end of each facts.
    - The source link should be with nofollow tag. Please follow this strictly. example: <li>Home pregnancy tests are about 97-99% accurate if instructions are followed carefully. <a href="https://www.cdc.gov/nchs/fastats/births.htm" target="_blank" rel="noreferrer noopener nofollow">source: CDC</a></li>
    
    '''

    gpt_response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content":  prompt,
            },
            # {"role": "user", "content": f"topic: {topic}, list of articles: {list_of_article}, number of facts: {num_facts} "},
        ],
        max_tokens=max_tokens,
        n=1,
        stop=None,
        temperature=temperature,
    )

    response = gpt_response["choices"][0]["message"]["content"].strip()

    # response = response.split("\n")  # Split the response by lines

    # filtered_facts = []
    # for fact in response:
    #     if any(pattern in fact.lower() for pattern in ["million", "%", "billion", "thousands"]) or re.match(r".*\b\d+[\d\w]*\b.*", fact):
    #         filtered_facts.append(fact)

    # filtered_facts = filtered_facts[:20]  # Select only the first 10 filtered facts
    # response = "\n".join(filtered_facts)  # Join the selected facts into a single string
    
    # st.write(num_facts)
    return response


def filter_final_response(response):

    websites = [
    "healthline",
    "medicalnewstoday",
    "verywellhealth",
    "mayoclinic",
    "webmd",
    "womenshealthmag",
    "stylecraze",
    "timesofindia.indiatimes",
    "food.ndtv",
    "thespruceeats",
    "organicfacts",
    "healthbenefitstimes",
    "ayurveda-foryou"
]
    
    filtered_final_response_list = []
    response_string_list = response.split('\n')
    # st.write(response_string_list)
    for fact in response_string_list:

        contains_keyword = False

        for website in websites:
            if website in fact:
                contains_keyword = True
                # st.write("true")
                break

        if not contains_keyword:
            filtered_final_response_list.append(fact)
                

    return '\n'.join(filtered_final_response_list)


def generate_facts_box(keyword, num_facts):
    concated_keyword = concate_query(keyword)
    scrap_query_df = scrape_google(concated_keyword)
    filtered_url_df = filtered_url(scrap_query_df)
    num_facts = num_facts
    
    for index, row in filtered_url_df.iterrows():
        url = row["Filtered Url"]
        try:
            if "ncbi.nlm.nih.gov" in url:
                article_text = get_article(url)
            else:
                article_text = scrape_article(url)
                
            filtered_url_df.at[index, "Article Text"] = re.sub('\s+', ' ', article_text).strip()
        except:
            filtered_url_df.at[index, "Article Text"] = ""

    article_text_list = []
    unique_urls = set()  # Set to store unique URLs

    for index, row in filtered_url_df.iterrows():
        url = row["Filtered Url"]
        article_text = row["Article Text"]
        if article_text and url not in unique_urls:
            article_text_list.append([url, article_text])
            unique_urls.add(url)

    # st.write(article_text_list)
    # st.write(article_text_list)
    
    st.write(filtered_url_df)



    token_count = count_tokens(article_text_list, concated_keyword, num_facts)
    # st.write(token_count)


    facts = generate_facts(article_text_list, concated_keyword, num_facts)

    # st.write(facts)
    filtered_fact = filter_final_response(facts)

    st.header("Filtered facts")
    st.write(filtered_fact)


def main():
    st.title("PharmEasy Fact-Box Generator")
    st.header("Enter A Keyword and see the magic!!")
    keyword = st.text_input("Enter a Keyword")
    user_api_key =  st.text_input("Enter Your OPENAI API Key", type="password")
    num_facts = st.number_input("Enter your desired numbers of facts", min_value=0, max_value=100, value=10, step=1)
    if st.button("Generate Facts"):
        if user_api_key:
            openai.api_key = user_api_key
            with st.spinner("Generating Facts..."):
                 generate_facts_box(keyword, num_facts)
        else:
            st.warning("Please enter your OpenAI API key above.")

if __name__ == '__main__':
    main()
