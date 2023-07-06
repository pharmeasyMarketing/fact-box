import streamlit as st

def main():
    st.title("PharmEasy Fact-Box")
    st.header("Simpy Enter A Keyword and we will provide you facts related to that keyword!!")
    keyword = st.text_input("Enter a Keyword")

    
    if st.button("Generate Keywords"):
        st.write("Coming Soon!! We Are Working On It")

if __name__ == '__main__':
    main()
