import pandas as pd
from lifelines import KaplanMeierFitter

from scipy.stats import (
    pearsonr,
    ttest_ind,
    f_oneway,
    chi2_contingency,
    linregress
)

from services.db_service import run_select_query


def understand_statistical_intent(user_query: str):
    query = user_query.lower()

    if "correlation" in query and "dose" in query and "os" in query:
        return {
            "method": "correlation",
            "table": "clinical_subjects",
            "columns": ["dose", "os"],
            "preprocessing": ["remove_nulls"],
            "sql": """
                SELECT dose, os
                FROM clinical_subjects
                WHERE dose IS NOT NULL
                AND os IS NOT NULL;
            """
        }

    if "average os" in query or "mean os" in query:
        return {
            "method": "mean_by_group",
            "table": "clinical_subjects",
            "columns": ["trtgrp", "os"],
            "group_by": "trtgrp",
            "preprocessing": ["remove_nulls"],
            "sql": """
                SELECT trtgrp, os
                FROM clinical_subjects
                WHERE trtgrp IS NOT NULL
                AND os IS NOT NULL;
            """
        }

    if "average pfs" in query or "mean pfs" in query:
        return {
            "method": "mean_by_group",
            "table": "clinical_subjects",
            "columns": ["trtgrp", "pfs"],
            "group_by": "trtgrp",
            "preprocessing": ["remove_nulls"],
            "sql": """
                SELECT trtgrp, pfs
                FROM clinical_subjects
                WHERE trtgrp IS NOT NULL
                AND pfs IS NOT NULL;
            """
        }

    if "standard deviation" in query or "std" in query:
        return {
            "method": "standard_deviation",
            "table": "clinical_subjects",
            "columns": ["os"],
            "preprocessing": ["remove_nulls"],
            "sql": """
                SELECT os
                FROM clinical_subjects
                WHERE os IS NOT NULL;
            """
        }

    if "anova" in query:
        return {
            "method": "anova",
            "table": "clinical_subjects",
            "columns": ["trtgrp", "os"],
            "group_by": "trtgrp",
            "preprocessing": ["remove_nulls"],
            "sql": """
                SELECT trtgrp, os
                FROM clinical_subjects
                WHERE trtgrp IS NOT NULL
                AND os IS NOT NULL;
            """
        }

    if "regression" in query:
        return {
            "method": "regression",
            "table": "clinical_subjects",
            "columns": ["dose", "os"],
            "preprocessing": ["remove_nulls"],
            "sql": """
                SELECT dose, os
                FROM clinical_subjects
                WHERE dose IS NOT NULL
                AND os IS NOT NULL;
            """
        }

    if "chi-square" in query or "chi square" in query:
        return {
            "method": "chi_square",
            "table": "clinical_subjects",
            "columns": ["gender", "trtgrp"],
            "preprocessing": ["remove_nulls"],
            "sql": """
                SELECT gender, trtgrp
                FROM clinical_subjects
                WHERE gender IS NOT NULL
                AND trtgrp IS NOT NULL;
            """
        }
    if "kaplan" in query or "survival analysis" in query:
        return {
            "method": "kaplan_meier",
            "table": "clinical_subjects",
            "columns": ["trtgrp", "os", "os_ind"],
            "group_by": "trtgrp",
            "preprocessing": ["remove_nulls"],
            "sql": """
                SELECT trtgrp, os, os_ind
                FROM clinical_subjects
                WHERE trtgrp IS NOT NULL
                AND os IS NOT NULL
                AND os_ind IS NOT NULL;
            """
        }

    if "compare" in query and "treatment" in query and "os" in query:
        return {
            "method": "t_test",
            "table": "clinical_subjects",
            "columns": ["trtgrp", "os"],
            "group_by": "trtgrp",
            "preprocessing": ["remove_nulls"],
            "sql": """
                SELECT trtgrp, os
                FROM clinical_subjects
                WHERE trtgrp IS NOT NULL
                AND os IS NOT NULL;
            """
        }

    return {
        "method": "unknown"
    }


def handle_statistical_query(user_query: str):
    intent = understand_statistical_intent(user_query)

    if intent["method"] == "unknown":
        return {
            "agent": "statistical_agent",
            "message": "Statistical query not recognized."
        }

    rows = run_select_query(intent["sql"])
    df = pd.DataFrame(rows)

    if df.empty:
        return {
            "agent": "statistical_agent",
            "method": intent["method"],
            "message": "No data available for this statistical analysis.",
            "sql": intent["sql"]
        }

    if intent["method"] == "correlation":
        correlation, p_value = pearsonr(df["dose"], df["os"])

        return {
            "agent": "statistical_agent",
            "method": "Pearson Correlation",
            "sql": intent["sql"],
            "columns_used": intent["columns"],
            "correlation": correlation,
            "p_value": p_value,
            "interpretation": "Measures relationship between dose and overall survival."
        }

    if intent["method"] == "mean_by_group":
        group_col = intent["group_by"]
        value_col = intent["columns"][1]

        result = (
            df.groupby(group_col)[value_col]
            .mean()
            .reset_index()
        )

        return {
            "agent": "statistical_agent",
            "method": "Mean By Group",
            "sql": intent["sql"],
            "group_by": group_col,
            "results": result.to_dict(orient="records"),
            "interpretation": f"Calculated average {value_col.upper()} grouped by {group_col}."
        }

    if intent["method"] == "standard_deviation":
        std_value = df["os"].std()

        return {
            "agent": "statistical_agent",
            "method": "Standard Deviation",
            "sql": intent["sql"],
            "columns_used": intent["columns"],
            "standard_deviation": std_value,
            "interpretation": "Measures variability in Overall Survival."
        }

    if intent["method"] == "anova":
        groups = []

        for grp in df["trtgrp"].dropna().unique():
            values = df[df["trtgrp"] == grp]["os"].dropna()
            if len(values) > 1:
                groups.append(values)

        if len(groups) < 2:
            return {
                "agent": "statistical_agent",
                "method": "ANOVA",
                "message": "Not enough groups with sufficient data for ANOVA.",
                "sql": intent["sql"]
            }

        f_stat, p_value = f_oneway(*groups)

        return {
            "agent": "statistical_agent",
            "method": "ANOVA",
            "sql": intent["sql"],
            "columns_used": intent["columns"],
            "f_statistic": f_stat,
            "p_value": p_value,
            "interpretation": "ANOVA compares mean OS across treatment groups."
        }

    if intent["method"] == "regression":
        slope, intercept, r_value, p_value, std_err = linregress(
            df["dose"],
            df["os"]
        )

        return {
            "agent": "statistical_agent",
            "method": "Linear Regression",
            "sql": intent["sql"],
            "columns_used": intent["columns"],
            "slope": slope,
            "intercept": intercept,
            "r_squared": r_value ** 2,
            "p_value": p_value,
            "std_error": std_err,
            "interpretation": "Linear regression models the relationship between dose and OS."
        }

    if intent["method"] == "chi_square":
        contingency = pd.crosstab(
            df["gender"],
            df["trtgrp"]
        )

        chi2, p_value, dof, expected = chi2_contingency(contingency)

        return {
            "agent": "statistical_agent",
            "method": "Chi-Square Test",
            "sql": intent["sql"],
            "columns_used": intent["columns"],
            "chi_square": chi2,
            "p_value": p_value,
            "degrees_of_freedom": dof,
            "interpretation": "Tests association between gender and treatment group."
        }
    
    if intent["method"] == "kaplan_meier":
        kmf = KaplanMeierFitter()

        survival_results = []

        for group_name in df["trtgrp"].dropna().unique():
            group_df = df[df["trtgrp"] == group_name]

            if group_df.empty:
                continue

            kmf.fit(
                durations=group_df["os"],
                event_observed=group_df["os_ind"],
                label=str(group_name)
            )

            survival_results.append({
                "treatment_group": str(group_name),
                "median_survival": kmf.median_survival_time_,
                "timeline": kmf.survival_function_.reset_index().head(10).to_dict(orient="records")
            })

        return {
            "agent": "statistical_agent",
            "method": "Kaplan-Meier Survival Analysis",
            "sql": intent["sql"],
            "columns_used": intent["columns"],
            "results": survival_results,
            "interpretation": "Kaplan-Meier estimates survival probability over time for each treatment group."
        }   

    if intent["method"] == "t_test":
        groups = df["trtgrp"].dropna().unique()

        if len(groups) < 2:
            return {
                "agent": "statistical_agent",
                "message": "Not enough treatment groups for t-test."
            }

        group_1 = df[df["trtgrp"] == groups[0]]["os"].dropna()
        group_2 = df[df["trtgrp"] == groups[1]]["os"].dropna()

        stat, p_value = ttest_ind(
            group_1,
            group_2,
            nan_policy="omit"
        )

        return {
            "agent": "statistical_agent",
            "method": "Independent T-Test",
            "sql": intent["sql"],
            "groups_compared": [
                str(groups[0]),
                str(groups[1])
            ],
            "t_statistic": stat,
            "p_value": p_value,
            "interpretation": "Compared OS between treatment groups."
        }