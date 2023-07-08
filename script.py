import streamlit as st
import requests
import os
from bs4 import BeautifulSoup, Tag
import pandas as pd
import urllib.parse
from newspaper import Article
import openai


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
    "https://www.ahrq.gov/"
    ]

    # flag = 0
    # for index, row in df.iterrows():
    #     url = row["URL"]
    #     for website in website_list:
    #         if website in url:
    #             df.loc[flag, "Filtered Url"] = url
    #             flag += 1       
    # return df
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

def pubmed_article_scrap(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        p_tags = soup.find_all('p')
        text_content = [tag.get_text() for tag in p_tags]
        return text_content
    except:
        return ""


# def generate_facts(list_of_article, topic, model="gpt-3.5-turbo-32k", max_tokens=500, temperature=0.2):

#     prompt = f'''
#     You are a specialized medical researcher or practitioner. A collection of articles titled '{list_of_article}' that delve into the subject matter of '{topic}' has been handed to you. Each article comes with the web page source from which the data has been procured. Your role involves conducting a detailed review and comprehension of these articles, discarding any superfluous information, and subsequently drawing out 10 significant data-driven facts pertaining to the provided topic. Each fact needs to be brief, straightforward, and formatted as a one-liner. These facts are to be organized in a numbered list with the accompanying source link for each fact, denoting the domain name of the source website.

#     Guidelines:
#     - Ensure the facts are grounded in data, incorporating quantifiable numbers or percentages as much as possible.
#     - shorten and keep the points crisp and strictly under 10 words.
#     - If fact is about any research consducted which is clinically not proved. Never add that fact.
#     - The facts should be arranged in an ordered, numbered list.
#     - Each fact should include the source in the format '[source: [domain_name](URL)]'. Replace 'domain_name' with the actual domain name from the list of articles, and 'URL' with the complete URL from the article list. The source should be hyperlinked with the anchor text representing the source name.
#     - You are strictly prohibited from creating an extra sources section. Instead, hyperlink the URL in the anchor text at the end of each fact.

#     ''' 

#     gpt_response = openai.ChatCompletion.create(
#         model=model,
#         messages=[
#             {
#                 "role": "system",
#                 "content":  prompt,
#             },
#             {"role": "user", "content": f"topic: {topic}, list of articles: {list_of_article} "},
#         ],
#         max_tokens=max_tokens,
#         n=1,
#         stop=None,
#         temperature=temperature,
#     )
#     response = gpt_response["choices"][0]["message"]["content"].strip()
#     response = response
#     return response



def generate_facts(list_of_article, topic, model="gpt-3.5-turbo-16k", max_tokens=500, temperature=0.2):
    if len(list_of_article) > 15500:
        # Split the list_of_article into three parts
        part_length = len(list_of_article) // 3
        list_of_article_part1 = list_of_article[:part_length]
        list_of_article_part2 = list_of_article[part_length:2*part_length]
        list_of_article_part3 = list_of_article[2*part_length:]
        
        # Generate facts for each part
        response_part1 = generate_facts_helper(list_of_article_part1, topic, model, max_tokens, temperature)
        response_part2 = generate_facts_helper(list_of_article_part2, topic, model, max_tokens, temperature)
        response_part3 = generate_facts_helper(list_of_article_part3, topic, model, max_tokens, temperature)
        
        # Combine the responses
        response = response_part1 + response_part2 + response_part3
    else:
        response = generate_facts_helper(list_of_article, topic, model, max_tokens, temperature)
    
    return response


import re
import openai

import re
import openai

def generate_facts_helper(list_of_article, topic, model, max_tokens, temperature):
    prompt = '''
    You are a specialized medical researcher or practitioner. A collection of articles titled '{list_of_article}' that delve into the subject matter of '{topic}' has been handed to you. Each article comes with the web page source from which the data has been procured. Your role involves conducting a detailed review and comprehension of these articles, discarding any superfluous information, and subsequently drawing out 5 crisp points of facts with statistics / numbers only, to the provided topic. Each fact needs to be straightforward, and formatted under 10 words. These facts are to be organized in a numbered list with the accompanying source link for each fact, denoting the domain name of the source website.

    Guidelines:
    - Shorten and keep the points crisp and strictly under 10 words.
    - If a fact is about any research conducted which is clinically not proved, never add that fact.
    - The facts should be arranged in an ordered, numbered list.
    - Each fact should include the source in the format '[source: [domain_name](URL)]'. Replace 'domain_name' with the actual domain name from the list of articles, and 'URL' with the complete URL from the article list. The source should be hyperlinked with the anchor text representing the source name.
    - You are strictly prohibited from creating an extra sources section. Instead, hyperlink the URL in the anchor text at the end of each fact.
    '''

    gpt_response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content":  prompt,
            },
            {"role": "user", "content": f"topic: {topic}, list of articles: {list_of_article} "},
        ],
        max_tokens=max_tokens,
        n=1,
        stop=None,
        temperature=temperature,
    )

    response = gpt_response["choices"][0]["message"]["content"].strip()
    response = response.split("\n")  # Split the response by lines

    filtered_facts = []
    for fact in response:
        if any(pattern in fact.lower() for pattern in ["million", "%", "billion", "thousands"]) or re.match(r".*\b\d+[\d\w]*\b.*", fact):
            filtered_facts.append(fact)

    filtered_facts = filtered_facts[:10]  # Select only the first 10 filtered facts
    response = "\n".join(filtered_facts)  # Join the selected facts into a single string

    return response

def generate_facts_box(keyword):
    concated_keyword = concate_query(keyword)
    scrap_query_df = scrape_google(concated_keyword)
    filtered_url_df = filtered_url(scrap_query_df)

    for index, row in filtered_url_df.iterrows():
        url = row["Filtered Url"]
        try:
            if "ncbi.nlm.nih.gov" in url:
                article_text = pubmed_article_scrap(url)
            else:
                article_text = scrape_article(url)
                
            filtered_url_df.at[index, "Article Text"] = article_text
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
    facts = generate_facts(article_text_list, concated_keyword)
    


    st.write(filtered_url_df)

    st.write(facts)

def main():
    st.title("PharmEasy Fact-Box Generator")
    st.header("Enter A Keyword and see the magic!!")
    keyword = st.text_input("Enter a Keyword")
    user_api_key =  st.text_input("Enter Your OPENAI API Key", type="password")
    
    if st.button("Generate Facts"):
        if user_api_key:
            openai.api_key = user_api_key
            with st.spinner("Generating Facts..."):
                 final_facts = generate_facts_box(keyword)
        else:
            st.warning("Please enter your OpenAI API key above.")        
        final_facts = generate_facts_box(keyword)

if __name__ == '__main__':
    main()
