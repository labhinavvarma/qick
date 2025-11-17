import streamlit as st
import requests
from neo4j import GraphDatabase
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import time
import os
from dotenv import load_dotenv
import pandas as pd
import re
import json
import uuid
import urllib3
import traceback

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

# SF Assist API Configuration

# Neo4j Configuration - Load from environment or use defaults
NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://10.189.116.237:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "<pwd>")  # Replace <pwd> with actual password
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "poc1")

# Initialize session state
if 'show_response' not in st.session_state:
    st.session_state['show_response'] = False
if 'cortex_response' not in st.session_state:
    st.session_state['cortex_response'] = ''
if 'method' not in st.session_state:
    st.session_state['method'] = 'Snowflake-Cortex'
if 'model_id' not in st.session_state:
    st.session_state['model_id'] = ''
if 'prompt' not in st.session_state:
    st.session_state['prompt'] = ''
if 'session_id' not in st.session_state:
    st.session_state['session_id'] = str(uuid.uuid4())
if 'show_technique_type' not in st.session_state:
    st.session_state['show_technique_type'] = False
if 'node_out' not in st.session_state:
    st.session_state['node_out'] = ''

Cypher_query_graph_content = '''You are a powerful text to Cypher query generator. Please generate Cypher query for Neo4J based on the following context.
         context:
         Use below relationships REPORTS_TO, WORKS_ON, PLATFORM_CONTAINS , GCP_ASSOCIATED_DBs , GCP_CONTAINS_TBLs, AWS_ASSOCIATED_DBs

         You are an assistant in generating responses . Further below are not Graph relationships and consider using only when asked in prompt
         projects --> handled by --> It_Application_Owner
         projects --> owned by --> It_Application_Owner
         projects --> Hosted --> Platform_Key
         projects --> deployed --> Platform_Key


        Column Conditions for REPORTS_TO
        with emp
        MATCH (e1:Employee), (e2:Employee)
        WHERE e1.Name = TRIM(emp.name) AND e2.Name = TRIM(emp.manager)
        CREATE (e1)-[:REPORTS_TO]->(e2);

        Column Conditions for WORKS_ON
        With apm
        Match (e:Employee),(p:APM_Projects)
        Where e.Name = trim(apm.it_application_owner) and p.It_Application_Owner = trim(apm.it_application_owner)
        merge (e) - [:WORKS_ON] -> (p)

        Column Conditions for PLATFORM_CONTAINS
        With eda
        MATCH (e:EDA_Platform), (p:APM_Projects)
        WHERE e.Platform_Key = TRIM(eda.Platform_Key) AND p.Platform_Key = TRIM(eda.Platform_Key)
        MERGE (e)-[:PLATFORM_CONTAINS]->(p);

        Column Conditions for GCP_ASSOCIATED_DBs
        With gcpdb
        Match (db:GCP_DBs), (p:APM_Projects)
        WHERE db.Application_Id = TRIM(gcpdb.Application_ID) AND p.Number = TRIM(gcpdb.Application_ID)
        MERGE (p)-[:GCP_ASSOCIATED_DBs]->(db);

        Column Conditions for GCP_CONTAINS_TBLs
        With gcptbl
        Match (db:GCP_DBs), (tbl:GCP_TBLs)
        WHERE db.Db_Name = Trim(gcptbl.TABLE_CATALOG) AND tbl.Table_Catalog = Trim(gcptbl.TABLE_CATALOG)
        MERGE (db)-[:GCP_CONTAINS_TBLs]->(tbl);

        Column Conditions for AWS_ASSOCIATED_DBs
        With awsdb
        Match (db:AWS_DBs), (p:APM_Projects)
        WHERE db.Application_Id = Trim(awsdb.Application_ID) AND p.Number = Trim(awsdb.Application_ID)
        MERGE (p)-[:AWS_ASSOCIATED_DBs]->(db);

        Use below table to identify Employee columns.
        CREATE (n:Employee {
            Name: TRIM(emp.name),
            Company: TRIM(emp.company),
            Manager: TRIM(emp.manager),
            Manager_L3: TRIM(emp.manager_l3),
            Manager_L4: TRIM(emp.manager_l4),
            Manager_L5: TRIM(emp.manager_l5),
            Location: TRIM(emp.location),
            Business_Unit: TRIM(emp.business_unit),
            Cost_Center: TRIM(emp.cost_center),
            Is_Manager: TRIM(emp.is_manager),
            Title: TRIM(emp.title),
            Vendor_Company: TRIM(emp.vendor_company),
            Org = TRIM(emp.org)
        })

        use below columns to identify APM_Projects columns.  
        CREATE (n:APM_Projects {
        n.Anthem_Domain = apm.u_anthem_domain,
                n.Delivery_Strategy = apm.u_delivery_strategy,
                n.Primary_Production_Data_Center = apm.u_primary_production_data_center,
                n.Short_Description = apm.short_description,
                n.Install_Status = apm.install_status,
                n.Number = apm.number,
                n.Audit_Scope = apm.u_audit_scope,
                n.It_Application_Owner = apm.it_application_owner,
                n.It_Development_Manager = apm.it_development_manager,
                n.Owned_By = apm.owned_by,
                n.Technical_Primary = apm.u_technical_primary,
                n.Managed_By = apm.managed_by,
                n.Technical_Secondary_2 = apm.u_technical_secondary_2,
                n.Application_Type = apm.application_type,
                n.Bit_System_Type = apm.u_bit_system_type,
                n.Cloud_Disposition = apm.u_cloud_disposition,
                n.Cloud_Migration_Status = apm.u_cloud_migration_status,
                n.Cloud_Migration_Target_Date = apm.u_cloud_migration_target_date,
                n.Cloud_Migration_Type = apm.u_cloud_migration_type,
                n.Cloud_Service_Provider = apm.u_cloud_service_provider,
                n.Date_Of_Deployment = apm.u_date_of_deployment,
                n.Identified_For_Replacement_Retirement = apm.u_identified_for_replacement_retirement,
                n.Migration_Status = apm.u_migration_status,
                n.Decommission_Status = apm.u_decommission_status
        })

        Use below columns for EDA_Platform
        CREATE (n:EDA_Platform {
            Platform: TRIM(eda.Platform),
            Category: TRIM(eda.Category),
            Description: TRIM(eda.Description),
            Platform_Key: TRIM(eda.Platform_Key),
            Account_Type: TRIM(eda.Account_Type)
        })

        use below columns for Cost Data by APM
        CREATE (n:APM_COST_DATA {
        AWS_Account_ID:trim(cst.AWS_Account_ID),
        Account_Name:trim(cst.Account_Name),
        Service:trim(cst.Service),
        ResourceId:trim(cst.ResourceId),
        apm_id:trim(cst.apm_id),
        costcenter:trim(cst.costcenter),
        Sum_ChargeBackAmt:trim(cst.Sum_ChargeBackAmt),
        Sum_UsageAmt:trim(cst.Sum_UsageAmt)
        })

        Use  below columns for gcptbl
        CREATE (n:GCP_TBLs {
            Table_Catalog:Trim(gcptbl.TABLE_CATALOG),
            Table_Schema:Trim(gcptbl.TABLE_SCHEMA),
            Table_Name:Trim(gcptbl.TABLE_NAME),
            Table_Owner:Trim(gcptbl.TABLE_OWNER),
            Table_Type:Trim(gcptbl.TABLE_TYPE),
            Is_Transient:Trim(gcptbl.IS_TRANSIENT),
            Clustering_Key:Trim(gcptbl.CLUSTERING_KEY),
            Row_Count:Trim(gcptbl.ROW_COUNT),
            Bytes:Trim(gcptbl.BYTES),
            Retention_Time:Trim(gcptbl.RETENTION_TIME),
            Self_Referencing_Column_Name:Trim(gcptbl.SELF_REFERENCING_COLUMN_NAME),
            Reference_Generation:Trim(gcptbl.REFERENCE_GENERATION),
            User_Defined_Type_Catalog:Trim(gcptbl.USER_DEFINED_TYPE_CATALOG),
            User_Defined_Type_Schema:Trim(gcptbl.USER_DEFINED_TYPE_SCHEMA),
            User_Defined_Type_Name:Trim(gcptbl.USER_DEFINED_TYPE_NAME),
            Is_Insertable_Into:Trim(gcptbl.IS_INSERTABLE_INTO),
            Is_Typed:Trim(gcptbl.IS_TYPED),
            Commit_Action:Trim(gcptbl.COMMIT_ACTION),
            Created:Trim(gcptbl.CREATED),
            Last_Altered:Trim(gcptbl.LAST_ALTERED),
            Last_Ddl:Trim(gcptbl.LAST_DDL),
            Last_Ddl_By:Trim(gcptbl.LAST_DDL_BY),
            Auto_Clustering_On:Trim(gcptbl.AUTO_CLUSTERING_ON),
            Comment:Trim(gcptbl.COMMENT),
            Is_Temporary:Trim(gcptbl.IS_TEMPORARY),
            Is_Iceberg:Trim(gcptbl.IS_ICEBERG),
            Is_Dynamic:Trim(gcptbl.IS_DYNAMIC)
            })

            Use below tables for gcpdb
            CREATE (n:GCP_DBs {
            Db_Name:Trim(gcpdb.DB_Name),
            Is_Default:Trim(gcpdb.is_default),
            Is_Current:Trim(gcpdb.is_current),
            Origin:Trim(gcpdb.origin),
            Owner:Trim(gcpdb.owner),
            Application_Name:Trim(gcpdb.Application_Name),
            Application_Id:Trim(gcpdb.Application_ID),
            Ticket_Number:Trim(gcpdb.Ticket_Number),
            Comments:Trim(gcpdb.Comments),
            Options:Trim(gcpdb.options),
            Retention_Time:Trim(gcpdb.retention_time),
            Kind:Trim(gcpdb.kind),
            Budget:Trim(gcpdb.budget),
            Owner_Role_Type:Trim(gcpdb.owner_role_type),
            Created_On:Trim(gcpdb.created_on)
            })
           
            Use below tables for awsdb
            CREATE (n:AWS_DBs {
            Database_Name:Trim(awsdb.DATABASE_NAME),
            Size_Of_Db:Trim(awsdb.SIZE_OF_DB),
            Created:Trim(awsdb.CREATED),
            Application_Name:Trim(awsdb.Application_Name),
            Application_Id:Trim(awsdb.Application_ID),
            Ticket_Number:Trim(awsdb.Ticket_Number),
            Comments:Trim(awsdb.Comments)
            })

        Below are few examples questions and the corresponding Cypher queries:
    <example>
    Question: List All Apps in Richmond Data Center?
    Query: MATCH (a:APM_Projects) WHERE a.Primary_Production_Data_Center = "Richmond" RETURN a.Name AS Application_Name,a.Number as APM_ID
    </example>
    <example>
    Question: List All Apps in DnA1 Account?
    Query: MATCH (p:APM_Projects)-[:PLATFORM_CONTAINS]-(e:EDA_Platform) WHERE e.Category = "DnA1" RETURN p.Name as APM_Name, p.Number as APM_Number
    </example>
    <example>
    Question: List "Kambalapally, Venkat" Portfoloio of projects with the App Owner?
    Query:MATCH (e:Employee)-[:REPORTS_TO|:WORKS_ON]-(p:APM_Projects) WHERE e.Name = "Kambalapally, Venkat" RETURN e.Name as EMP_Name, p.Number as APM_Number,p.Name as APM_Name,p.It_Application_Owner
    </example>
    <example>
    Question: What is the cost for Project APM1010683?
    Query:MATCH (p:APM_Projects)-[:COST_BY_APM_ID]->(c:APM_COST_DATA) WHERE p.Number = "APM1010683" WITH p, SUM(TOINTEGER(c.Sum_ChargeBackAmt)) AS totalCost RETURN p.Name AS Application, totalCost
    </example>
    <example>
    Question: What is the cost of DnA1?
    Query:MATCH (p:APM_Projects)-[:PLATFORM_CONTAINS]-(e:EDA_Platform),(p)-[:COST_BY_APM_ID]-(c:APM_COST_DATA) WHERE e.Category = "DnA1" WITH SUM(TOINTEGER(c.Sum_ChargeBackAmt)) AS totalCost RETURN totalCost
    </example>
    <example>
    Question: List all contractors with venodrname under "Vishwakarma, Sanjay" resource?
    Query:match (e:Employee) where e.Title starts with "Contingent" and e.Manager="Vishwakarma, Sanjay" return e.Name,e.Manager,e.Title,e.Vendor_Company
    </example>
    <example>
    Question: Where is this APM1010683 running?
    Query:MATCH (e:Employee)-[:REPORTS_TO|:WORKS_ON]-(p:APM_Projects)-[:PLATFORM_CONTAINS|:COST_BY_APM_ID]-(eda:EDA_Platform),(p)-[:COST_BY_APM_ID]-(cost:APM_COST_DATA) WHERE p.Number = "APM1010683" RETURN e, p, eda, cost
    </example>
     <example>
    Question: How many contractors are under "Vishwakarma, Sanjay"?
    Query:match (e:Employee) where e.Title starts with "Contingent" and e.Manager="Rajamanickam, Madhu" return count(e.Name) as Contractor_count
    </example>
    <example>
    Question: Summarize about Kambalapally, Venkat portifolio and his reportee information
    Query:MATCH (e:Employee)-[:REPORTS_TO|:WORKS_ON]-(p:APM_Projects) WHERE e.Name = "Kambalapally, Venkat" OR e.Manager = "Kambalapally, Venkat" WITH e, COLLECT(DISTINCT p) AS projects RETURN e.Name AS Employee_Name, e.Title AS Employee_Title, e.Manager AS Manager,SIZE(projects) AS Number_of_Projects,[p IN projects | p.Name] AS Project_Names,[p IN projects | p.It_Application_Owner] AS Project_Owners
    </example>
    
    IMPORTANT: Your response must contain ONLY the Cypher query wrapped in ```cypher``` code blocks. Do not include any explanations or additional text.
'''.strip()


def cortex_exec(model_id, prompt, Cypher_query_graph_content, form_select):
    """Execute query using SF Assist API"""
    session_id = str(uuid.uuid4())
    full_prompt = f"{Cypher_query_graph_content}\n\nQuestion: {prompt}\nAnswer:"
    
    payload = {
        "query": {
            "aplctn_cd": APLCTN_CD,
            "app_id": APP_ID,
            "api_key": API_KEY,
            "method": "cortex",
            "model": model_id,
            "sys_msg": SYS_MSG,
            "limit_convs": "0",
            "prompt": {
                "messages": [
                    {"role": "user", "content": full_prompt}
                ]
            },
            "app_lvl_prefix": "",
            "user_id": "edadip_user",
            "session_id": session_id
        }
    }
    
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Accept": "application/json",
        "Authorization": f'Snowflake Token="{API_KEY}"'
    }
    
    try:
        print(f"Calling SF Assist API with model: {model_id}")
        response = requests.post(API_URL, headers=headers, json=payload, verify=False)
        
        if response.status_code == 200:
            raw = response.text
            if "end_of_stream" in raw:
                answer, _, _ = raw.partition("end_of_stream")
                cortex_response = answer.strip()
            else:
                cortex_response = raw.strip()
            
            print(f"✅ SF Assist API response received")
            print(f"Response preview: {cortex_response[:500]}")  # Debug logging
            
            if form_select == "model-form":
                st.session_state['cortex_response'] = cortex_response
            
            return cortex_response
        else:
            error_msg = f"❌ Error {response.status_code}: {response.text}"
            print(error_msg)
            st.error(error_msg)
            return None
    except Exception as e:
        error_msg = f"❌ Request failed: {str(e)}"
        print(error_msg)
        traceback.print_exc()
        st.error(error_msg)
        return None


def run_query(query_ip):
    """Execute Cypher query on Neo4j"""
    print(f"Cypher Query Execution - {query_ip} ----------")
    try:
        with GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)) as driver:
            driver.verify_connectivity()
            with driver.session(database=NEO4J_DATABASE) as session:
                graph_response = session.run(query_ip)
                df = pd.DataFrame([record.data() for record in graph_response])
                return df
    except Exception as e:
        error_msg = f"Neo4j Error: {str(e)}"
        print(error_msg)
        st.error(error_msg)
        return pd.DataFrame()


def clear_query():
    """Clear query-related session state"""
    st.session_state.show_response = False
    st.session_state.show_technique_type = False


def extract_cypher_query(input_string):
    """Extract Cypher query from various formats - IMPROVED VERSION"""
    if not input_string:
        return None
    
    print(f"DEBUG: Attempting to extract query from: {input_string[:200]}...")
    
    # Try 1: Extract from ```cypher ... ```
    pattern = r"```cypher\s*(.*?)\s*```"
    match = re.search(pattern, input_string, re.DOTALL | re.IGNORECASE)
    if match:
        cypher_query = match.group(1).strip()
        single_line_query = ' '.join(cypher_query.split())
        print(f"✅ Extracted from ```cypher block: {single_line_query[:100]}...")
        return single_line_query
    
    # Try 2: Extract from ``` ... ``` (without language specifier)
    pattern = r"```\s*(MATCH.*?)\s*```"
    match = re.search(pattern, input_string, re.DOTALL | re.IGNORECASE)
    if match:
        cypher_query = match.group(1).strip()
        single_line_query = ' '.join(cypher_query.split())
        print(f"✅ Extracted from ``` block: {single_line_query[:100]}...")
        return single_line_query
    
    # Try 3: Find any line that starts with MATCH, CREATE, MERGE, etc.
    cypher_keywords = ['MATCH', 'CREATE', 'MERGE', 'RETURN', 'WITH', 'WHERE']
    lines = input_string.split('\n')
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if any(line_stripped.upper().startswith(keyword) for keyword in cypher_keywords):
            # Found a Cypher query line, now collect all related lines
            query_lines = [line_stripped]
            
            # Collect subsequent lines that look like part of the query
            for j in range(i+1, len(lines)):
                next_line = lines[j].strip()
                if not next_line or next_line.startswith('#') or next_line.startswith('//'):
                    continue
                if any(kw in next_line.upper() for kw in ['MATCH', 'WHERE', 'RETURN', 'WITH', 'AND', 'OR', 'CREATE', 'MERGE', 'SET']):
                    query_lines.append(next_line)
                elif next_line.endswith(';'):
                    query_lines.append(next_line.rstrip(';'))
                    break
                else:
                    # Check if it's a continuation of the previous line
                    if query_lines and not next_line.startswith('['):
                        query_lines.append(next_line)
            
            cypher_query = ' '.join(query_lines)
            single_line_query = ' '.join(cypher_query.split())
            print(f"✅ Extracted from text search: {single_line_query[:100]}...")
            return single_line_query
    
    # Try 4: Look for "Query:" label
    pattern = r"Query:\s*(.*?)(?:\n\n|$)"
    match = re.search(pattern, input_string, re.DOTALL | re.IGNORECASE)
    if match:
        cypher_query = match.group(1).strip()
        single_line_query = ' '.join(cypher_query.split())
        print(f"✅ Extracted from Query: label: {single_line_query[:100]}...")
        return single_line_query
    
    # Try 5: If the entire response looks like a query
    cleaned = input_string.strip()
    if cleaned.upper().startswith(tuple(cypher_keywords)):
        single_line_query = ' '.join(cleaned.split())
        print(f"✅ Entire response is query: {single_line_query[:100]}...")
        return single_line_query
    
    print(f"❌ Could not extract Cypher query from response")
    return None


def main():
    # Title
    st.markdown("<h1 style='text-align: center;'>Chat with EDA Ontology Data</h1>", unsafe_allow_html=True)
    
    # Display image if exists
    if os.path.exists("kg.png"):
        st.image("kg.png")
    
    st.markdown("""<style>.big-font { font-size:300px !important;}</style>""", unsafe_allow_html=True)
    
    # Method selection (only Snowflake-Cortex now)
    method = st.selectbox(
        ":blue[Choose LLM Platform]",
        ('Snowflake-Cortex',),
        on_change=clear_query
    )
    
    # Create form for user input
    model_form = st.form("model-form")
    
    # Model selection subheader
    model_form.subheader("Ask using Cortex to generate Cypher Query")
    
    # Model dropdown selection
    model = model_form.selectbox(
        ":blue[Select your model]:",
        (
            "Llama3.1-70B",
            "Mistral-Large",
            "Mixtral-8x7b",
            "Mistral-7b",
            "Gemma-7b",
            "Arctic",
            "Reka"
        ),
    )
    
    # Map display names to model IDs
    model_mapping = {
        "Llama3.1-70B": "llama3.1-70b",
        "Mistral-Large": "mistral-large",
        "Mixtral-8x7b": "mixtral-8x7b",
        "Mistral-7b": "mistral-7b",
        "Gemma-7b": "gemma-7b",
        "Arctic": "snowflake-arctic",
        "Reka": "reka-flash"
    }
    
    model_id = model_mapping[model]
    
    # Prompt input
    prompt = model_form.text_input(
        "Enter prompt",
        placeholder="Provide Prompt",
        label_visibility="collapsed"
    )
    
    # Submit button
    submit_button = model_form.form_submit_button("Submit", on_click=clear_query)
    
    # Handle submission
    if submit_button:
        st.session_state['method'] = method
        st.session_state['model_id'] = model_id
        st.session_state['prompt'] = prompt
        st.session_state['show_response'] = True
        print(submit_button)
        
        # Execute LLM request
        if method == 'Snowflake-Cortex':
            cortex_exec_res = cortex_exec(model_id, prompt, Cypher_query_graph_content, "model-form")
    
    # Display results
    if st.session_state['show_response']:
        method = st.session_state['method']
        model_id = st.session_state['model_id']
        prompt = st.session_state['prompt']
        
        # Display model response
        st.subheader("Generated Response:")
        model_answer = st.empty()
        if method == 'Snowflake-Cortex':
            model_answer.write(st.session_state['cortex_response'])
        
        # Reset session button in sidebar
        if st.sidebar.button("Reset Session"):
            st.session_state.clear()
            st.success("Information reset successfully!")
            st.rerun()
        
        # Extract Cypher query
        cortex_query_ip = st.session_state['cortex_response']
        print(f"Full response for extraction: {cortex_query_ip}")
        
        # Extract the query using the improved function
        query_ip = extract_cypher_query(cortex_query_ip)
        
        # Display extracted query or error
        if query_ip:
            st.success("✅ Cypher Query Extracted Successfully!")
            st.code(query_ip, language="cypher")
            print("Extracted Cypher Query:")
            print(query_ip)
            
            # Display options in sidebar
            technique_type = st.sidebar.radio(
                "**Display Record Selection**",
                ["Total Rows", "Tabular Display", "Graph Display"]
            )
            
            print("Final query is", query_ip)
            
            if technique_type == "Total Rows":
                # Count query
                try:
                    cnt_query = query_ip.split("RETURN")[0] + " RETURN count(*) as Total_Rows"
                    print("the res is", cnt_query)
                    cnt_result = run_query(cnt_query)
                    print(cnt_result)
                    st.subheader("📊 Total Rows")
                    st.write(cnt_result)
                except Exception as e:
                    st.error(f"Error creating count query: {str(e)}")
                
            elif technique_type == "Tabular Display":
                # Execute query and display results
                st.subheader("📊 Query Results")
                query_result = run_query(query_ip)
                if not query_result.empty:
                    st.write(query_result)
                    st.info(f"Total records: {len(query_result)}")
                else:
                    st.warning("No results found")
                
            elif technique_type == "Graph Display":
                print("Graph view selected")
                st.subheader("🕸️ Graph Visualization")
                st.info("Opening Neo4j Browser to display graph...")
                
                url = "http://10.189.116.237:7474/browser/"
                username = NEO4J_USER
                password = NEO4J_PASSWORD
                database = NEO4J_DATABASE
                
                db_xpath = "//*[@id='MAIN_WRAPPER_DOM_ID']/div/div[3]/div[1]/article/div[2]/div[2]/div/div/div[2]/div/form/div[2]/label/input"
                uname_xpath = "//*[@id='MAIN_WRAPPER_DOM_ID']/div/div[3]/div[1]/article/div[2]/div[2]/div/div/div[2]/div/form/div[4]/label/input"
                pwd_xpath = "//*[@id='MAIN_WRAPPER_DOM_ID']/div/div[3]/div[1]/article/div[2]/div[2]/div/div/div[2]/div/form/div[5]/label/input"
                submit_xpath = "//*[@id='MAIN_WRAPPER_DOM_ID']/div/div[3]/div[1]/article/div[2]/div[2]/div/div/div[2]/div/form/span/button"
                query_input_xpath = "//div[@id='monaco-main-editor']/..//div[contains(@class,'cursor monaco-mouse-cursor-text')]"
                execute_button_xpath = "//button[@data-testid='editor-Run']"
                
                try:
                    driver = webdriver.Chrome()
                    driver.get("http://10.189.116.237:7474/browser/")
                    driver.maximize_window()
                    actions = ActionChains(driver)
                    time.sleep(5)
                    
                    db_field = driver.find_element(By.XPATH, db_xpath)
                    db_field.send_keys(database)
                    print("Entered Database")
                    time.sleep(5)
                    
                    uname_field = driver.find_element(By.XPATH, uname_xpath)
                    uname_field.send_keys(username)
                    print("Entered User Name")
                    time.sleep(5)
                    
                    pwd_field = driver.find_element(By.XPATH, pwd_xpath)
                    pwd_field.send_keys(password)
                    print("Entered Password")
                    time.sleep(5)
                    
                    submit_button_elem = driver.find_element(By.XPATH, submit_xpath)
                    submit_button_elem.click()
                    print("Clicked Submit button")
                    time.sleep(10)
                    
                    query_input = driver.find_element(By.XPATH, query_input_xpath)
                    print("Found query Input")
                    time.sleep(10)
                    
                    actions.move_to_element(query_input).click().send_keys(query_ip).perform()
                    print("Moved to input and Clicked on it")
                    print("Entered Query")
                    time.sleep(5)
                    
                    execute_button = driver.find_element(By.XPATH, execute_button_xpath)
                    execute_button.click()
                    print("Clicked on Execute button")
                    print("Output shown successfully")
                    
                    st.success("✅ Query executed in Neo4j Browser!")
                    time.sleep(300)
                except Exception as e:
                    st.error(f"Error in Graph Display: {str(e)}")
                    print(f"Error in Graph Display: {str(e)}")
            
            else:
                print("Nothing selected")
        else:
            st.error("⚠️ Could not extract Cypher query from the response.")
            st.info("💡 The LLM response might not contain a valid Cypher query. Try rephrasing your question or check the response format above.")
            
            # Show debug expander
            with st.expander("🔍 Debug: View Raw Response"):
                st.text(cortex_query_ip)


if __name__ == "__main__":
    main()
