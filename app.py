import pandas as pd
import streamlit as st
import plotly.express as px
import os


st.set_page_config(page_title="Tenant Review Performance Monitor", layout="wide")


# Load data

@st.cache_data
def load_data():
    businesses = pd.read_csv("businesses.csv")
    reviews = pd.read_csv("reviews.csv")
    yearly = pd.read_csv("yearly_metrics.csv")

    reviews["review_date"] = pd.to_datetime(reviews["review_date"], errors="coerce")
    yearly["review_year"] = pd.to_numeric(yearly["review_year"], errors="coerce")

    businesses["business_name"] = businesses["business_name"].fillna("").astype(str).str.strip()
    reviews["business_name"] = reviews["business_name"].fillna("").astype(str).str.strip()
    reviews["platform"] = reviews["platform"].fillna("").astype(str).str.strip().str.title()
    yearly["platform"] = yearly["platform"].fillna("").astype(str).str.strip().str.title()

    businesses["display_name"] = businesses["business_name"]
    reviews["display_name"] = reviews["business_name"]
    yearly["display_name"] = yearly["business_name"]

    return businesses, reviews, yearly


businesses, reviews, yearly = load_data()


# Header

st.title("Tenant Review Performance Monitor")
st.caption("A portfolio prototype that translates a real Excel-based tenant review workflow into a focused decision-support app")


# Business selector

selector_controls_col1, selector_controls_col2 = st.columns([1, 2])

with selector_controls_col1:
    sort_option = st.selectbox(
        "Sort businesses by",
        ["Name (A-Z)", "Risk level", "Review count", "Average rating"],
    )

with selector_controls_col2:
    search_term = st.text_input(
        "Search businesses",
        placeholder="Type part of a business name..."
    ).strip().lower()

risk_sort_map = {"High": 0, "Medium": 1, "Low": 2}
business_selector_df = businesses.copy()
business_selector_df["risk_sort"] = business_selector_df["risk_flag"].map(risk_sort_map).fillna(3)
business_selector_df["review_count_sort"] = business_selector_df["total_reviews"].fillna(0)
business_selector_df["avg_rating_sort"] = business_selector_df["avg_rating_overall"].fillna(-1)

if search_term:
    business_selector_df = business_selector_df[
        business_selector_df["display_name"].fillna("").str.lower().str.contains(search_term, na=False)
    ].copy()

if sort_option == "Risk level":
    business_selector_df = business_selector_df.sort_values(["risk_sort", "display_name"])
elif sort_option == "Review count":
    business_selector_df = business_selector_df.sort_values(
        ["review_count_sort", "display_name"], ascending=[False, True]
    )
elif sort_option == "Average rating":
    business_selector_df = business_selector_df.sort_values(
        ["avg_rating_sort", "display_name"], ascending=[False, True]
    )
else:
    business_selector_df = business_selector_df.sort_values(["display_name"])

business_list = business_selector_df["display_name"].dropna().unique()

if len(business_list) == 0:
    st.warning("No businesses match your search.")
    st.stop()

default_business = "Kazu's Sushi"

if default_business in business_list:
    default_index = list(business_list).index(default_business)
else:
    default_index = 0

selected_business = st.selectbox("Select a business", business_list, index=default_index)

selected_business_row = businesses[businesses["display_name"] == selected_business].iloc[0]
selected_business_id = selected_business_row["business_id"]

# Filter reviews and yearly data for the selected business
business_reviews = reviews[reviews["business_id"] == selected_business_id].copy()
business_yearly = yearly[yearly["business_id"] == selected_business_id].copy()


# KPI cards

col1, col2, col3, col4, col5 = st.columns(5)

avg_rating = selected_business_row.get("avg_rating_overall", None)
rating_delta = selected_business_row.get("rating_delta_platform", None)
pct_negative = selected_business_row.get("pct_negative_overall", None)
risk_flag = selected_business_row.get("risk_flag", "N/A")
review_count = len(business_reviews)

col1.metric("Average Rating", f"{avg_rating:.2f}" if pd.notna(avg_rating) else "N/A")
col2.metric("Total Reviews", f"{review_count:,}")
col3.metric("Platform Rating Gap", f"{rating_delta:.2f}" if pd.notna(rating_delta) else "N/A")
col4.metric("Negative Review Rate", f"{pct_negative:.1%}" if pd.notna(pct_negative) else "N/A")
col5.metric("Risk Level", str(risk_flag))

st.divider()

st.caption("Automated synthesis of customer sentiment and operational risk signals")

# AI summary panel

st.subheader("AI Summary")

performance_phrase = "strong"
if pd.notna(avg_rating):
    if avg_rating < 3.5:
        performance_phrase = "weak"
    elif avg_rating < 4.1:
        performance_phrase = "mixed"

negative_reviews = business_reviews[business_reviews["is_negative"] == 1].copy()
recent_reviews = business_reviews.sort_values("review_date", ascending=False).head(8)

summary_parts = []

if pd.notna(avg_rating) and pd.notna(pct_negative):
    summary_parts.append(
        f"Overall performance is {performance_phrase}, with an average rating of {avg_rating:.2f} across {review_count:,} reviews and {pct_negative:.1%} negative feedback."
    )
elif pd.notna(avg_rating):
    summary_parts.append(
        f"Overall performance is {performance_phrase}, with an average rating of {avg_rating:.2f} across {review_count:,} reviews."
    )

if pd.notna(rating_delta):
    if rating_delta > 0.3:
        summary_parts.append(
            "Google performs meaningfully better than Yelp, which suggests a modest platform perception gap rather than a broad reputation problem."
        )
    elif rating_delta < -0.3:
        summary_parts.append(
            "Yelp performs meaningfully better than Google, which suggests a modest platform perception gap rather than a broad reputation problem."
        )
    else:
        summary_parts.append(
            "Google and Yelp are relatively aligned, which suggests customer sentiment is fairly consistent across platforms."
        )

summary_parts.append(f"Current risk level is {risk_flag}.")

common_negative_terms = []
if not negative_reviews.empty and "review_text" in negative_reviews.columns:
    stopwords = {
        "the", "and", "for", "that", "this", "with", "they", "were", "have", "had",
        "but", "not", "you", "are", "was", "too", "very", "our", "all", "from",
        "place", "just", "get", "got", "out", "about", "there", "their", "them",
        "would", "will", "been", "when", "what", "your", "has", "more", "than",
        "didn", "doesn", "dont", "cant", "couldn", "shouldn", "then", "back", "said",
        "told", "came", "went", "make", "made", "still", "even", "also", "really",
        "into", "over", "only", "after", "before", "because", "while", "where", "being",
        "having", "install", "installed"
    }
    negative_text = (
        negative_reviews["review_text"]
        .dropna()
        .astype(str)
        .str.lower()
        .str.replace(r"[^a-z\s]", " ", regex=True)
        .str.split()
    )
    tokens = [word for words in negative_text for word in words if len(word) > 3 and word not in stopwords]
    if tokens:
        common_negative_terms = pd.Series(tokens).value_counts().head(5).index.tolist()

if common_negative_terms:
    summary_parts.append(
        "Frequent terms in negative reviews suggest recurring issues related to " + ", ".join(common_negative_terms) + "."
    )
elif len(negative_reviews) > 0:
    summary_parts.append(
        f"There are {len(negative_reviews):,} negative reviews, which suggests some recurring service friction even though overall risk remains {str(risk_flag).lower()}."
    )

st.write(" ".join(summary_parts))

api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    with st.expander("Generate LLM summary from recent reviews"):
        st.caption("Uses the most recent reviews for the selected business. Requires API key.")
        if st.button("Generate AI summary"):
            try:
                from openai import OpenAI

                client = OpenAI(api_key=api_key)
                review_snippets = recent_reviews[["platform", "rating", "review_text"]].fillna("")
                review_block = "\n\n".join(
                    [
                        f"Platform: {row.platform}\nRating: {row.rating}\nReview: {row.review_text}"
                        for row in review_snippets.itertuples(index=False)
                    ]
                )
                prompt = (
                    "You are analyzing customer reviews for a commercial tenant. "
                    "Write a concise business-facing summary with three parts: overall sentiment, key positives, and key risks. "
                    "Interpret the data instead of just repeating it. Use plain English, avoid hype, and keep it under 150 words.\n\n"
                    f"Business: {selected_business}\n\nReviews:\n{review_block}"
                )
                response = client.responses.create(
                    model="gpt-4.1-mini",
                    input=prompt,
                )
                st.success(response.output_text)
            except Exception as e:
                st.error(f"AI summary failed: {e}")
else:
    st.caption("To enable live AI summarization, set an OPENAI_API_KEY environment variable before running Streamlit.")

st.divider()


# Charts

left, right = st.columns(2)

with left:
    st.subheader("Average Rating Over Time")
    rating_chart_df = business_yearly.dropna(subset=["review_year", "avg_rating"]).copy()
    rating_chart_df["review_year"] = rating_chart_df["review_year"].astype(int)

    if not rating_chart_df.empty:
        fig_rating = px.line(
            rating_chart_df,
            x="review_year",
            y="avg_rating",
            color="platform",
            markers=True,
            title="Average Rating by Year"
        )
        st.plotly_chart(fig_rating, width="stretch")
    else:
        st.info("No rating trend data available.")

with right:
    st.subheader("Negative Reviews Over Time")
    negative_chart_df = business_yearly.dropna(subset=["review_year", "negative_review_count"]).copy()
    negative_chart_df["review_year"] = negative_chart_df["review_year"].astype(int)

    if not negative_chart_df.empty:
        fig_negative = px.bar(
            negative_chart_df,
            x="review_year",
            y="negative_review_count",
            color="platform",
            barmode="group",
            title="Negative Review Count by Year"
        )
        st.plotly_chart(fig_negative, width="stretch")
    else:
        st.info("No negative review trend data available.")

st.subheader("Platform Performance Differences")

platform_compare = (
    business_reviews.groupby("platform", dropna=False)
    .agg(
        average_rating=("rating", "mean"),
        review_count=("rating", "count"),
        negative_reviews=("is_negative", "sum"),
    )
    .reset_index()
)

if not platform_compare.empty:
    platform_compare["pct_negative"] = platform_compare["negative_reviews"] / platform_compare["review_count"]
    fig_compare = px.scatter(
        platform_compare,
        x="review_count",
        y="average_rating",
        size="negative_reviews",
        color="platform",
        color_discrete_map={
            "Google": "#0F9D58",
            "Yelp": "#c41200"
        },
        hover_data={
            "platform": True,
            "review_count": True,
            "average_rating": ":.2f",
            "negative_reviews": True,
            "pct_negative": ":.1%"
        },
        title="Platform Comparison: Rating vs Review Volume"
    )
    fig_compare.update_layout(xaxis_title="Number of Reviews", yaxis_title="Average Rating")
    st.plotly_chart(fig_compare, width="stretch")

    display_compare = platform_compare.rename(columns={
        "platform": "Platform",
        "average_rating": "Average Rating",
        "review_count": "Number of Reviews",
        "negative_reviews": "Negative Reviews",
        "pct_negative": "% Negative"
    }).copy()
    display_compare["Average Rating"] = display_compare["Average Rating"].round(2)
    display_compare["% Negative"] = (display_compare["% Negative"] * 100).round(1).astype(str) + "%"
    st.dataframe(display_compare, use_container_width=True, hide_index=True)
else:
    st.info("No platform comparison data available.")

st.divider()

with st.expander("Recent review samples"):
    sample_reviews = recent_reviews[["review_date", "platform", "rating", "review_text"]].copy()
    sample_reviews["review_date"] = pd.to_datetime(sample_reviews["review_date"], errors="coerce").dt.strftime("%Y-%m-%d")
    sample_reviews = sample_reviews.rename(columns={
        "review_date": "Review Date",
        "platform": "Platform",
        "rating": "Rating",
        "review_text": "Review Text"
    })
    st.dataframe(sample_reviews, use_container_width=True, hide_index=True)