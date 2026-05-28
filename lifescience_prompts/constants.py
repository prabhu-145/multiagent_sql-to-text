import json
from typing import List

PROMPT_DETAILS: str = (
    "It is important that the SQL query complies with MySQL syntax. "
    "During join if column names are the same, please use an alias, e.g., llm.customer_id in the SELECT statement. "
    "It is also important to respect the type of columns: if a column is a string, the value should be enclosed in quotes. "
    "While concatenating a non-string column, make sure to cast the column to string. "
    "For date columns comparing to a string, please cast the string input. "
    "If you have enough data for generating the SQL query using a single table, use only that table. "
    "Please take care of the table names, use only the table names that are in the schema. Go through the table and column descriptions carefully and frame the SQL queries accordingly. I want the business context like this, consider this as a reference '''Search all the clinical Subjects in the data view. Filter down the clinical subjects that have samples of the following biomarker types - nanostring and circulating tumor DNA. Nanostring is selected because it represents gene expression data, and circulating tumor DNA is selected because it represents somatic mutation. Count the subjects based on the availability of these biomarker types'''. "
    "Please don't go for complex SQL logics for all the questions. "
    "If just one table is enough for answering the user query, then don't go for joins. "
    "Don't come up with your own table names. "
    "Take distinct of derivativeid instead of subjectid in sample_inventory_va_view table. "
    "Please give alias names for the columns in sql query."
    "Only return your SQL query, nothing more! Think step by step."
    "Cast to float type while handling numerical columns.follwo this strictly"
)

BIOMARKER_KEYWORDS: List[str] = [
    "JAK2",
    "STAT1",
    "CD57",
    "IL-6",
    "ABCB1",
    "CD4",
    "IL-2",
    "CD8",
    "IFN-gamma",
    "PD-L1",
]

REPORT_EXAMPLES: List[str] = [
    "✅ Compare mutation VAF for EGFR across treatment arms",
    "✅ Which biomarkers differ significantly between baseline and post-treatment?",
    "✅ Is there a statistically significant change in VAF_CFB for responders?",
    "✅ Perform DEA using vaf_cfb between Europe and Asia region subjects",
    "✅ What genes are differentially expressed between males and females?",
    "✅ Compare gene expression between responders vs non-responders",
    "✅ Please do a DEA analysis based on the following parameters - Nanostring data, disease stage",
    "✅ Analyse circulating tumor DNA (ctDNA) data based on gender distribution for variant allele frequency change from baseline",
    "✅ Analyze the differences in EGFR expression levels across groups: percentage of VAF mutations, and non-mutated EGFR patients?",
    "✅ Are there differences in VAF between subjects who received different treatments?",
    "✅ Which biomarkers show the highest standard deviation in gene expression across different treatment group categories?",
    "✅ I want to run a DEA analysis on nanostring data. Analysis groups should be based on Treatment Group",
    "✅ I want to run a DEA analysis on DNAseq data. Split by Reponse Status, and base results on Number of Allels",
    "✅ Where is my VAF comparison report?",
    "✅ Show completed DEA analyses",
    "✅ Give me list of analytics reports",
    "✅ How many analytics reports are completed",
    "✅ analytics reports?",
    "✅ link to download analytics reports",
    "✅ show list of analysis run by me",
    "✅ What is the report status for the biomarker analysis from the Phase 1 trial?",
    "✅ Check the status of the clinical trial report",
    "❌ Summarize adverse events by treatment group",
    "❌ What is the distribution of subjects by gender?",
    "❌ List all sites in the study",
    "❌ Show AE counts by severity",
    "❌ Find patients with high IL6 levels",
    "❌ Explain what STAT1 biomarker does",
]


def get_analytics_questions() -> str:
    return """
    DEA Questions:
        - Please do a DEA analysis based on the following parameters - Nanostring data, disease stage
        - Analyse circulating tumor DNA (ctDNA) data based on gender distribution for variant allele frequency change from baseline.
        - Summarize  the percentage changes from the baseline in EGFR VAF between groups with detected versus non-detected EGFR mutations at enrolment using DEA
        - Are there differences in VAF between subjects who received different treatment
        - Summarize the differences across regions in terms of biomarker expression on drug treatment.
        - Run DEA analysis for IHC biomarker with statistically significant differential expression changes between responders and non-responders?
        - Which biomarkers show the highest standard deviation in gene expression across different treatment group   categories?
        - generate a summary report comparing the raw cell counts across disease stages
        - Analyse specific treatment groups that show particularly high or low normalized cell counts in comparison to others?
        - Are there significant differences in EGFR expression between samples with low versus high VAFs of EGFR mutations?
        - What are the genes that differentially expressed between subjects of first two visits
        - Are there difference in Nanostring gene expression	changes between treatment groups?.
        - Perform DEA to identify ctDNA genes differentially expressed across disease categories.
        - Run differential expression analysis of IHC markers between response groups.
        - Conduct DEA of IHC  expression between AE and non AE group
        - Perform differential analysis of ctDNA VAF grouped by response status.
        - Assess differential expression of Nanostring genes by response status.
        - Evaluate regional differences in ctDNA VAF expression using DEA.
        - Identify differentially expressed Nanostring genes by region via DEA.
        - Run DEA of IHC markers across regional populations.
        - Perform DEA to identify baseline ctDNA VAF differentially expressed by response category.
        - Conduct DEA to identify baseline IHC expression differences across response categories..
        - Evaluate day 21 differential expression of Nanostring markers across response categories.
        - Compare the changes in ctdna van at day 15 between AE and non-AE subjects using DEA.
        - Assess post-dose changes in IHC expression relative to day 15 by enrolment dose.
        - Run DEA on Nanostring gene expression changes at day 21 by enrollment dose.


    Correlation Questions:
        - Summarize how ctDNA VAF correlates with response status across all patients.
        - Describe the relationship between Nanostring expression and treatment group using correlation analysis.
        - What is the correlation between disease stage and ctDNA variant allele frequency (VAF)?
        - Perform correlation for mutation detection rates in ctDNA correlated biomarkers with gender identity?
        - What is the statistical correlation between a region and the presence of ctDNA mutations?
        - Run a correlation analysis between nanostring biomareker data and disease stage.
        - Run a correlation analysis between PD-L1 IHC expression and treatment group?
        - What is the correlation between ctDNA VAF and the adverse events?
        - Perform correlation analysis between IHC-based biomarker scores and therapy
        - What is the statistical correlation between FC biomarker data and treatment group outcomes?
        - What is a correlation between ctDNA VAF and IHC biomarker data in predicting patient response status?
        - Perform correlation analysis, between NanoString and ctDNA VAF in patients with different TreatmentGroup?
        - Run correlation Analysis between IHC and Nanostring biomarker data with gender?
        - How do NanoString gene expression and flow cytometry cell populations correlate with region?
        - What is correlation between mutation biomarker (Ctdna) data and FC data with response statust



    PCA Questions:
        - Assess whether Nanostring expression patterns help distinguish patients by therapy type  using PCA scores.
        - Summarize IHC biomarker data contributes to PCA components in relation to region.
        - Identify any trends between Flow Cytometry-based PCA loadings and patient gender.
        - Summarize how ctDNA VAF patterns align with treatment group in PCA-transformed data.
        - Report whether Nanostring expression is predictive of disease type based on its loading in the first principal component.
        - Summarize whether QC align with PCA components driven by Nanostring and clinical data.
        - Run PCA  for  Flow Cytometry markers contribute to the treatment groups
        - Perform PCA components that associate Flow Cytometry data with gender
        - Summarize how FC-based PCA scores reflect progression-free survival (pfs) across patient response status
        - Analyze how IHC expression patterns align with treatment  group in PCA
        """
