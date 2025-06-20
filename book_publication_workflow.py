
import asyncio
from playwright.async_api import async_playwright
import re
from datetime import datetime
import os
import glob

# Simulated LLM functions
def simulate_llm_spin(content):
    """Pretend to rewrite the story by changing some words."""
    replacements = {
        "beautiful": "stunning",
        "ran": "hurried",
        "said": "declared",
        "good": "excellent"
    }
    spun_content = content
    for old, new in replacements.items():
        spun_content = spun_content.replace(old, new)
    return spun_content

def simulate_llm_review(content):
    """Pretend to check the story and give advice."""
    return f"Reviewed content: {content}\n[AI Reviewer Note]: Make sentences clearer."

# Scraper Agent
async def scrape_content(url, screenshot_path):
    """Grab story text and take a picture of the webpage."""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url)
        content = await page.locator("#mw-content-text").inner_text()
        content = re.sub(r'\s+', ' ', content).strip()
        await page.screenshot(path=screenshot_path)
        await browser.close()
        return content

# Human-in-the-Loop Functions
def get_human_feedback(content, role):
    """Ask a person to give feedback or approve the story."""
    print(f"\n{role}, please look at this:\n{content[:200]}...\n")
    feedback = input(f"Enter feedback for {role} (or type 'approve' to move on): ")
    if feedback.lower() != "approve":
        with open(f"{role}_feedback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", "w") as f:
            f.write(feedback)
        return feedback
    return None

def apply_human_feedback(content, feedback):
    """Add the person’s feedback to the story."""
    if feedback:
        return f"{content}\n[Added feedback: {feedback}]"
    return content

# File-Based Storage
def store_version(content, version_id, collection):
    """Save the story to a file instead of ChromaDB."""
    with open(f"version_{version_id}.txt", "w", encoding="utf-8") as f:
        f.write(content)

# File-Based Search
def rl_search(collection, query, n_results=1):
    """Return the latest saved file content."""
    files = glob.glob("version_*.txt")
    if files:
        with open(max(files, key=os.path.getctime), "r", encoding="utf-8") as f:
            return f.read()
    return None

# Main Workflow
async def publication_workflow(url):
    """Run the whole process from start to finish."""
    collection = None  # No ChromaDB needed
    
    # Grab the story
    screenshot_path = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    original_content = await scrape_content(url, screenshot_path)
    print(f"Got the story! Screenshot saved at {screenshot_path}")
    
    version_id = f"v1_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    store_version(original_content, version_id, collection)
    
    # Rewrite the story
    spun_content = simulate_llm_spin(original_content)
    print("\nRewritten story:\n", spun_content[:200], "...")
    
    # Get writer feedback
    writer_feedback = get_human_feedback(spun_content, "Writer")
    spun_content = apply_human_feedback(spun_content, writer_feedback)
    version_id = f"v2_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    store_version(spun_content, version_id, collection)
    
    # Review the story
    reviewed_content = simulate_llm_review(spun_content)
    print("\nReviewed story:\n", reviewed_content[:200], "...")
    
    # Get reviewer feedback
    reviewer_feedback = get_human_feedback(reviewed_content, "Reviewer")
    reviewed_content = apply_human_feedback(reviewed_content, reviewer_feedback)
    version_id = f"v3_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    store_version(reviewed_content, version_id, collection)
    
    # Get editor feedback
    editor_feedback = get_human_feedback(reviewed_content, "Editor")
    final_content = apply_human_feedback(reviewed_content, editor_feedback)
    version_id = f"v4_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    store_version(final_content, version_id, collection)
    
    # Find the final story
    final_version = rl_search(collection, final_content)
    print("\nFinal Story:\n", final_version[:200], "...")
    
    return final_content

# Run the workflow
if __name__ == "__main__":
    url = "https://en.wikisource.org/wiki/The_Gates_of_Morning/Book_1/Chapter_1"
    asyncio.run(publication_workflow(url))
