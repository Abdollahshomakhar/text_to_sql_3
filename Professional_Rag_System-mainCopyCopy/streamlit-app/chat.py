API_KEY = "YOUR_API_KEY"
from llama_index.llms.openai_like import OpenAILike

llm = OpenAILike(
    model="qwen/qwen3-32b",
    api_base="https://openrouter.ai/api/v1",
    api_key=API_KEY,
    is_chat_model=True,
)
from llama_index.core import VectorStoreIndex
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# استفاده از مدل embed محلی از HuggingFace
embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
import chromadb
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import StorageContext
from llama_index.core import VectorStoreIndex
chroma_client = chromadb.PersistentClient(path="./chroma_db1")
chroma_collection = chroma_client.get_or_create_collection("docs")

vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

storage_context = StorageContext.from_defaults(vector_store=vector_store)

index1 = VectorStoreIndex.from_vector_store(
    vector_store,
    storage_context=storage_context,
    embed_model=embed_model   # 👈 اینجا هم باید باشد
)
query_engine = index1.as_query_engine(llm=llm)
# 0
response = query_engine.query("""
Generate ONLY SQL.

Find clients whose payments is less than 100.

Use only existing tables and existing columns from the provided schema.
Never invent columns.
""")
print(response.response) 
import streamlit as st

# ---------------- Page ----------------
st.set_page_config(page_title="SQL RAG", layout="centered")

st.title("🗄️ SQL RAG Assistant")

question = st.text_area(
    "Question",
    value="Find clients whose payments is less than 100.",
    height=120
)

if st.button("Generate SQL"):

    prompt = f"""
Generate ONLY SQL.

{question}

Use only existing tables and existing columns from the provided schema.
Never invent columns.
"""

    with st.spinner("Generating SQL..."):
        response = query_engine.query(prompt)

    st.subheader("Generated SQL")

    st.code(response.response, language="sql")

import mysql.connector
import pandas as pd

def connect_db():
    return mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="13818181eq",
        database="sql_invoicing"
    )
# ذخیره SQL تولید شده
st.session_state["generated_sql"] = response.response
# ---------------- Execute SQL ----------------

if "generated_sql" in st.session_state:

    st.subheader("Generated SQL")

    st.code(st.session_state["generated_sql"], language="sql")

    if st.button("▶️ Run SQL"):

        try:
            conn = connect_db()
            cursor = conn.cursor()

            sql = st.session_state["generated_sql"].strip()

            cursor.execute(sql)

            # اگر SELECT بود
            if sql.lower().startswith("select"):
                rows = cursor.fetchall()
                columns = [col[0] for col in cursor.description]

                df = pd.DataFrame(rows, columns=columns)

                st.success(f"{len(df)} rows returned.")
                st.dataframe(df, use_container_width=True)

            else:
                conn.commit()
                st.success(f"{cursor.rowcount} rows affected.")

            cursor.close()
            conn.close()

        except Exception as e:
            st.error(str(e))