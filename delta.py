from email import header
import streamlit as st
import requests
from neo4j import GraphDatabase
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import time
import streamlit.components.v1 as components
import neo4j
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


# Initialize session state
if 'show_response' not in st.session_state:
    st.session_state['show_response'] = False
if 'cortex_response' not in st.session_state:
    st.session_state['cortex_response'] = ''
if 'model_id' not in st.session_state:
    st.session_state['model_id'] = ''
if 'prompt' not in st.session_state:
    st.session_state['prompt'] = ''
if 'session_id' not in st.session_state:
    st.session_state['session_id'] = str(uuid.uuid4())

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
    Query:MATCH (p:APM_Projects)-[:COST_BY_APM_ID]->(c:APM_COST_DATA) WHERE p.Number = "APM1010683" WITH p, SUM(TOINTEGER(c.Sum_ChargeBackAmt)) AS totalCost
RETURN p.Name AS Application, totalCost
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
    Query:MATCH (e:Employee)-[:REPORTS_TO|:WORKS_ON]-(p:APM_Projects) WHERE e.Name = "Kambalapally, Venkat" OR e.Manager = "Kambalapally, Venkat" WITH e, COLLECT(DISTINCT p) AS projects     RETURN e.Name AS Employee_Name, e.Title AS Employee_Title, e.Manager AS Manager,SIZE(projects) AS Number_of_Projects,[p IN projects | p.Name] AS Project_Names,[p IN projects | p.It_Application_Owner] AS Project_Owners
    </example>
            '''.strip()


def cortex_exec(model_id, prompt, Cypher_query_graph_content):
    """Execute query using SF Assist API"""
    
    # Build messages
    messages = [
        {"role": "system", "content": SYS_MSG},
        {"role": "user", "content": Cypher_query_graph_content},
        {"role": "user", "content": f"Question: {prompt}\nAnswer:"}
    ]
    
    # Build SF Assist API payload with correct data types
    payload = {
        "query": {
            "aplctn_cd": APLCTN_CD,
            "app_id": APP_ID,
            "api_key": API_KEY,
            "method": "cortex",
            "model": model_id,
            "sys_msg": SYS_MSG,
            "limit_convs": 0,  # Changed from "0" to 0 (integer)
            "prompt": {
                "messages": messages
            },
            "app_lvl_prefix": "",
            "user_id": "edadip_user",
            "session_id": st.session_state['session_id']
        }
    }
    
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Accept": "application/json",
        "Authorization": f'Snowflake Token="{API_KEY}"'
    }
    
    try:
        print(f"Calling SF Assist API with model: {model_id}")
        print(f"Session ID: {st.session_state['session_id']}")
        
        response = requests.post(API_URL, headers=headers, json=payload, verify=False)
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            raw = response.text
            print(f"Raw response (first 200 chars): {raw[:200]}")
            
            # Parse response
            if "end_of_stream" in raw:
                answer, _, _ = raw.partition("end_of_stream")
                cortex_response = answer.strip()
            else:
                cortex_response = raw.strip()
            
            print(f"SF Assist API response received successfully")
            st.session_state['cortex_response'] = cortex_response
            
            return cortex_response
        else:
            error_msg = f"SF Assist API Error {response.status_code}: {response.text}"
            print(error_msg)
            st.error(error_msg)
            return error_msg
            
    except Exception as e:
        error_msg = f"Error calling SF Assist API: {str(e)}"
        print(error_msg)
        traceback.print_exc()
        st.error(error_msg)
        return error_msg


def run_query(query_ip):
    """Execute Cypher query on Neo4j"""
    print(f"Executing Cypher Query: {query_ip}")
    URI = "neo4j://10.189.116.237:7687"
    try:
        with GraphDatabase.driver(URI, auth=("neo4j", "<pwd>")) as driver:
            driver.verify_connectivity()
            with driver.session(database='poc1') as session:
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


def extract_cypher_query(input_string):
    """Extract Cypher query from markdown code blocks"""
    if not input_string:
        return None
        
    pattern = r"```cypher(.*?)```"
    match = re.search(pattern, input_string, re.DOTALL)
    
    if match:
        cypher_query = match.group(1).strip()
        single_line_query = ' '.join(cypher_query.split())
        return single_line_query
    else:
        # If no code block found, return the input as-is (might already be a query)
        return input_string.strip()


def main():
    st.markdown("<h1 style='text-align: center;'>Chat with EDA Ontology Data</h1>", unsafe_allow_html=True)
    
    # Check if image exists before trying to display
    if os.path.exists("kg.png"):
        st.image("kg.png")
    
    st.markdown("""<style>.big-font { font-size:300px !important;}</style>""", unsafe_allow_html=True)
    
    model_form = st.form("model-form")
    
    # Model selection for Snowflake Cortex
    model_form.subheader("Ask using Cortex to generate Cypher Query")
    model = model_form.selectbox(
        ":blue[Select your model]:",
        (
            "Mistral-Large",
            "Mixtral-8x7b",
            "Llama3",
            "Mistral-7b",
            "Gemma-7b",
            "Arctic",
            "Reka"
        ),
    )
    
    # Map display names to model IDs
    model_mapping = {
        "Mistral-Large": "mistral-large",
        "Mixtral-8x7b": "mixtral-8x7b",
        "Mistral-7b": "mistral-7b",
        "Llama3": "llama3.1-70b",
        "Gemma-7b": "gemma-7b",
        "Arctic": "snowflake-arctic",
        "Reka": "reka-flash"
    }
    model_id = model_mapping[model]
    
    # Prompt input
    prompt = model_form.text_input(
        "Enter prompt",
        placeholder="e.g., List all Apps in Richmond Data Center",
        label_visibility="collapsed"
    )
    
    submit_button = model_form.form_submit_button("Submit", on_click=clear_query)
    
    # Handle submission
