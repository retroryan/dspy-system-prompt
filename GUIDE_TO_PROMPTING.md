# Guide to Prompting: What Works and What Doesn't

## Quick Start: The Golden Rule

**Be specific about what you want.** The system understands natural language, but it needs concrete details to work with. Think of it like talking to a knowledgeable assistant who needs clear instructions rather than hints.

## What Works Well

### For Real Estate Searches

#### ✅ Good Prompts

**Specific Feature Searches:**
- "Find modern family homes with pools in Oakland under $800k"
- "Show me luxury condos with city views in San Francisco"
- "Search for townhouses with home offices near BART stations"

**Neighborhood Research:**
- "Tell me about the Rockridge neighborhood in Oakland"
- "What amenities does the Mission District in San Francisco offer?"
- "Describe the culture and lifestyle of Temescal"

**School-Focused Searches:**
- "Find family homes near top-rated elementary schools in Berkeley"
- "Show me properties in areas with good public schools"
- "Search for homes in school districts with STEM programs"

**Lifestyle-Based Queries:**
- "Find a quiet home good for remote work with fast internet"
- "Show me walkable neighborhoods with coffee shops and parks"
- "Search for pet-friendly condos with outdoor space"

#### ❌ Poor Prompts

**Too Vague:**
- "I need a house"
- "Show me something nice"
- "What's available?"

**Life Stories:**
- "I'm a software engineer who just got married and we're thinking about kids someday"
- "My journey to homeownership started when I was young"
- "Let me tell you about my family situation"

**Impossible Requests:**
- "Show me property PROP-XYZ-123" (specific IDs that don't exist)
- "Find me the house from that movie"
- "Show me what will be built next year"

### For E-commerce Shopping

#### ✅ Good Prompts

**Product Searches:**
- "Find gaming laptops under $1500 with RTX graphics"
- "Show me wireless headphones with noise cancellation"
- "Search for ergonomic office chairs with lumbar support"

**Order Management:**
- "Show me all my delivered orders"
- "What's the status of my recent orders?"
- "Find my orders from last month"

**Cart Operations:**
- "Add the highest-rated gaming keyboard to my cart"
- "Remove the cheapest item from my cart"
- "Show me what's in my shopping cart"

#### ❌ Poor Prompts

**No Context:**
- "Buy that thing"
- "The one I was looking at yesterday"
- "You know what I mean"

**Multiple Unrelated Actions:**
- "Order a laptop, return my shoes, and tell me about weather"
- "Do everything at once"

### For Agriculture and Weather

#### ✅ Good Prompts

**Weather Queries:**
- "What's the weather in Des Moines, Iowa?"
- "Compare weather between Chicago and Denver"
- "Show me the 7-day forecast for Sacramento"

**Agricultural Decisions:**
- "Should I plant corn today in Iowa based on the weather?"
- "What are the soil conditions for planting in Fresno?"
- "Is it a good time to harvest wheat in Kansas?"

#### ❌ Poor Prompts

**Missing Location:**
- "What's the weather?"
- "Should I plant crops?"
- "Is it going to rain?"

## Understanding the Limitations

### The System Cannot:

1. **Remember things you haven't told it in this conversation**
   - Won't know about houses you viewed last week
   - Can't recall products you mentioned in a different session
   - Doesn't have access to your browsing history

2. **Access external websites or services**
   - Can't check Zillow or Redfin
   - Won't pull data from Amazon or eBay
   - Doesn't browse the internet

3. **Make predictions about the future**
   - Can't predict market prices
   - Won't forecast inventory changes
   - Doesn't know about upcoming listings

4. **Handle multiple unrelated tasks in one query**
   - Keep each request focused on one goal
   - Don't mix different tool sets (real estate + shopping + weather)

### The System Can:

1. **Understand context within a conversation**
   - Remembers what you asked earlier in the same session
   - Can refine searches based on previous queries
   - Builds on information you've provided

2. **Interpret natural language intelligently**
   - Understands "cozy" means small and comfortable
   - Knows "near transit" means close to public transportation
   - Recognizes "family-friendly" implies certain features

3. **Combine multiple criteria**
   - Can search with price, location, and features together
   - Handles complex filters simultaneously
   - Balances different requirements

## Pro Tips for Better Results

### 1. Start Broad, Then Narrow

**First Query:** "Show me family homes in Oakland"
**Follow-up:** "Which of these have pools?"
**Refine:** "Focus on ones under $900k"

### 2. Use Location Names, Not Codes

**Good:** "Search in San Francisco, California"
**Avoid:** "Search in SF" or "Search in 94102"

### 3. Be Explicit About Price Ranges

**Good:** "Between $500k and $800k"
**Better:** "Under $800k with at least 3 bedrooms"
**Avoid:** "Affordable" or "Not too expensive"

### 4. Specify What's Important

Instead of: "Find me a nice house"
Try: "Find a quiet single-family home with a large backyard for kids"

### 5. One Thing at a Time

Instead of: "Find a house, check my orders, and what's the weather?"
Try these separately:
1. "Find family homes in Berkeley"
2. "Show me my recent orders"
3. "What's the weather in Berkeley?"

## Examples of Conversations That Work

### Real Estate Journey

**Query 1:** "Find modern homes with pools in Oakland under $1 million"
*System shows results*

**Query 2:** "Tell me more about the Rockridge neighborhood"
*System provides neighborhood information*

**Query 3:** "Are there any of the homes from my first search in Rockridge?"
*System connects the context*

### Shopping Session

**Query 1:** "I need a laptop for gaming under $1500"
*System shows options*

**Query 2:** "Add the one with the best graphics card to my cart"
*System adds specific item*

**Query 3:** "Actually, show me desktop computers instead"
*System switches focus*

### Weather Planning

**Query 1:** "What's the weather forecast for Des Moines this week?"
*System provides forecast*

**Query 2:** "Based on this, when would be best to plant corn?"
*System analyzes conditions*

**Query 3:** "How does this compare to last year's planting conditions?"
*System provides comparison*

## Common Mistakes to Avoid

### 1. Assuming the System Knows Everything

**Wrong:** "Show me that house we talked about"
**Right:** "Show me the 4-bedroom house with a pool in Oakland we just discussed"

### 2. Using Informal Descriptions

**Wrong:** "Find something hipster-ish"
**Right:** "Find properties in artistic neighborhoods with vintage character"

### 3. Combining Incompatible Requests

**Wrong:** "Find a mansion under $200k"
**Right:** "Find the best house I can get for $200k"

### 4. Forgetting Context Switches

**Wrong:** Asking about real estate, then suddenly "Add it to cart"
**Right:** Switch tool sets explicitly or stay within one domain

## Quick Reference: Words That Work

### For Property Types
- Single-family home, condo, townhouse, apartment
- Modern, vintage, contemporary, traditional
- Luxury, affordable, starter home, fixer-upper

### For Features
- Pool, garage, home office, backyard
- Updated kitchen, hardwood floors, high ceilings
- View, natural light, open floor plan

### For Locations
- Specific city names (Oakland, San Francisco, Berkeley)
- Neighborhood names (Mission, Rockridge, Temescal)
- Near schools, near transit, walkable, quiet street

### For Shopping
- Under/over/between (for prices)
- Highest-rated, best-selling, newest
- Warranty, free shipping, in stock

## Remember

The system is like a knowledgeable assistant who needs clear instructions. It can't read your mind, but it can understand well-expressed needs. Be specific, be clear, and build your queries step by step for the best results.

When in doubt, imagine you're talking to a helpful real estate agent or shopping assistant who just met you - they're experts in their field but need you to tell them exactly what you're looking for.