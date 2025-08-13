# Complex Multi-Tool Agentic Loop Test Scenarios

## Overview
These test scenarios are designed to require multiple agentic loops, sophisticated reasoning, and chained tool execution. Each scenario tests the agent's ability to maintain context, make decisions based on intermediate results, and handle complex user requests that cannot be resolved with a single tool call.

## 1. Smart Product Replacement Workflow
**User Query:** "My gaming keyboard from order ORD001 stopped working. Find me a suitable replacement that's better but costs less than $100, and check if I've ordered similar products before."

**Expected Agent Behavior:**
1. Use `get_order` to retrieve order ORD001 details
2. Extract the product ID (KB456) and price ($89.99) from the order
3. Use `search_products` to find keyboards under $100
4. Use `list_orders` to check order history for john.smith@example.com
5. Analyze past orders for keyboard purchases to understand preferences
6. Compare ratings and features to recommend an upgrade
7. Use `add_to_cart` to add the recommended product
8. Synthesize a recommendation explaining why this is a better choice

**Complexity:** Requires memory of initial product, price comparison, historical analysis, and intelligent recommendation based on multiple data points.

## 2. Order Anomaly Detection and Resolution
**User Query:** "I'm emma.young@example.com. I think I might have duplicate orders or something weird with my recent purchases. Can you check if everything looks normal and flag any issues?"

**Expected Agent Behavior:**
1. Use `list_orders` to get all orders for emma.young@example.com
2. Analyze order dates and items for potential duplicates
3. Use `get_order` on each recent order to check details
4. Identify order ORD021 with unusually high value ($1599.97)
5. Use `track_order` to verify shipping status
6. Compare against typical order patterns
7. Flag the high-value order and verify items are intentional
8. Provide summary of findings with recommendations

**Complexity:** Requires pattern recognition, anomaly detection, and intelligent analysis of multiple data points.

## 3. Multi-Order Shipping Crisis Management
**User Query:** "I'm hosting an event this weekend and ordered multiple items. Check all my pending orders and tell me which ones won't arrive in time. For those that won't make it, find me same-day alternatives."

**Expected Agent Behavior:**
1. Use `list_orders` to find all orders for the user
2. Filter for non-delivered orders
3. Use `track_order` for each pending order to get delivery dates
4. Calculate which orders won't arrive before the weekend
5. Use `get_order` to identify specific products in delayed orders
6. Use `search_products` to find alternatives for each delayed item
7. Prioritize products with high stock levels for quick shipping
8. Use `add_to_cart` for urgent replacements
9. Provide comprehensive status report with solutions

**Complexity:** Requires date calculation, multiple conditional paths, and intelligent alternative selection.

## 4. Price Protection Audit
**User Query:** "Check if any products I bought in the last month have dropped in price by more than 20%. I want to know if I should have waited."

**Expected Agent Behavior:**
1. Use `list_orders` to get recent orders
2. Filter orders from the last 30 days
3. Use `get_order` for each order to extract product IDs and prices paid
4. Use `search_products` to find current prices for each product
5. Calculate price differences and percentages
6. Identify products with >20% price drops
7. Calculate total potential savings
8. Provide detailed report with specific items and amounts

**Complexity:** Requires date filtering, price comparison across time, percentage calculations, and aggregation.

## 5. Intelligent Bundle Recommendation
**User Query:** "I just bought a gaming laptop (order ORD004). What accessories should I get to complete my setup? My budget is $500 total."

**Expected Agent Behavior:**
1. Use `get_order` to retrieve ORD004 details
2. Identify the gaming laptop purchase
3. Use `list_orders` to check what accessories the user already owns
4. Use `search_products` for "gaming mouse" to find compatible accessories
5. Use `search_products` for "laptop case" for protection
6. Use `search_products` for "gaming keyboard" for desktop setup
7. Use `search_products` for "monitor" for dual-screen setup
8. Calculate optimal bundle within $500 budget
9. Prioritize based on ratings and compatibility
10. Use `add_to_cart` for recommended items
11. Explain the value and compatibility of each recommendation

**Complexity:** Requires understanding product relationships, budget optimization, and intelligent bundling.

## 6. Customer Loyalty Analysis
**User Query:** "Analyze my purchase history and tell me what product categories I'm most loyal to, and where I might be overpaying compared to alternatives."

**Expected Agent Behavior:**
1. Use `list_orders` to get complete order history
2. Use `get_order` for each order to extract detailed item information
3. Categorize purchases by product type
4. Calculate frequency and total spend per category
5. Identify most purchased categories
6. Use `search_products` to find cheaper alternatives for frequent purchases
7. Calculate potential savings with alternative products
8. Generate loyalty insights and savings recommendations

**Complexity:** Requires statistical analysis, categorization, pattern recognition, and cost optimization.

## 7. Inventory Warning System
**User Query:** "I want to reorder my usual items but only if they're in stock. Check my top 5 most ordered products and their current availability."

**Expected Agent Behavior:**
1. Use `list_orders` to get order history
2. Use `get_order` for multiple orders to extract product details
3. Build frequency map of purchased products
4. Identify top 5 most ordered items
5. Use `search_products` to check current stock for each item
6. Flag any low-stock items (< 10 units)
7. Suggest alternatives for out-of-stock items
8. Use `add_to_cart` for available items
9. Provide inventory status report with recommendations

**Complexity:** Requires frequency analysis, inventory checking, and conditional cart management.

## 8. Return and Replace Workflow
**User Query:** "Order ORD016 has the wrong keyboard. Find me the keyboard I actually wanted (it should have RGB and be wireless) and help me understand what went wrong."

**Expected Agent Behavior:**
1. Use `get_order` to check ORD016 details
2. Identify the delivered keyboard (KB789 - Pro Gaming Keyboard)
3. Analyze why it might be wrong (not wireless)
4. Use `search_products` for "wireless RGB keyboard"
5. Compare features to identify the intended product
6. Use `list_orders` to check if user has ordered wireless keyboards before
7. Identify the likely intended product (KB456)
8. Use `add_to_cart` for the correct product
9. Explain the mix-up and provide resolution steps

**Complexity:** Requires product feature analysis, intent inference, and error resolution.

## 9. Competitive Price Tracking
**User Query:** "I'm considering buying a 4K monitor. Check if I've bought monitors before, what I paid, and whether prices are better now or if I should wait."

**Expected Agent Behavior:**
1. Use `list_orders` to find previous monitor purchases
2. Use `get_order` to extract historical monitor prices
3. Use `search_products` for "4K monitor" to get current prices
4. Use `search_products` for "monitor" to get broader market prices
5. Compare historical prices with current prices
6. Analyze price trends (increasing/decreasing)
7. Check stock levels to assess urgency
8. Provide buy/wait recommendation with reasoning

**Complexity:** Requires historical analysis, price trend detection, and strategic recommendation.

## 10. Complex Gift Shopping Assistant
**User Query:** "I need to buy gifts for 3 people with a $200 total budget. One loves gaming, one needs office supplies, and one is into audio equipment. Find the best rated items that fit the budget."

**Expected Agent Behavior:**
1. Divide budget strategically (~$65-70 per person)
2. Use `search_products` for "gaming" with max_price=$70
3. Filter results by rating to find best gaming gift
4. Use `search_products` for "office" with max_price=$70
5. Select highly-rated office supplies
6. Use `search_products` for "audio" with max_price=$70
7. Choose best audio equipment within budget
8. Verify total is under $200
9. Adjust selections if over budget
10. Use `add_to_cart` for all three items
11. Provide gift summary with total cost and reasoning

**Complexity:** Requires budget allocation, multi-criteria optimization, and constraint satisfaction.

## Test Execution Notes

### Success Criteria
- Agent must use at least 3 different tools per scenario
- Agent must maintain context throughout the entire interaction
- Agent must make intelligent decisions based on intermediate results
- Agent must handle edge cases gracefully (out of stock, missing data, etc.)
- Agent must provide clear reasoning for recommendations

### Evaluation Metrics
1. **Tool Chain Accuracy**: Did the agent select the right sequence of tools?
2. **Context Preservation**: Did the agent remember information from earlier tool calls?
3. **Decision Quality**: Were the agent's choices logical given the available data?
4. **Error Handling**: How well did the agent handle missing or unexpected data?
5. **User Value**: Did the agent provide actionable and valuable insights?

### Expected Patterns
These scenarios should demonstrate:
- **Reactive Planning**: Agent adjusts strategy based on tool results
- **Information Synthesis**: Agent combines data from multiple sources
- **Intelligent Filtering**: Agent narrows down options based on constraints
- **Graceful Degradation**: Agent provides alternatives when ideal solution isn't available
- **Explanatory Power**: Agent explains its reasoning and recommendations

## Implementation Recommendations

1. **Trajectory Tracking**: Each scenario should generate a detailed trajectory showing:
   - Initial thought/reasoning
   - Tool selection rationale  
   - Result interpretation
   - Next step planning
   - Final synthesis

2. **Performance Benchmarks**:
   - Scenarios 1-3: Should complete in 3-5 loops
   - Scenarios 4-6: May require 5-7 loops
   - Scenarios 7-10: Could need 7-10 loops

3. **Failure Modes to Test**:
   - Product out of stock
   - Order not found
   - Email address not in system
   - Budget constraints impossible to meet
   - Conflicting requirements

4. **Enhanced Testing**:
   - Run each scenario with different temperature settings
   - Test with various users to ensure generalization
   - Verify consistency across multiple runs
   - Measure time to completion
   - Track token usage per scenario