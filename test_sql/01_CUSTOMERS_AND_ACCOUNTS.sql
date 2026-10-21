-- ======================================================================
-- TEST SCRIPT 1: 01_CUSTOMERS_AND_ACCOUNTS.sql
-- Contains 2 SELECT queries for Customers and Accounts
-- ======================================================================

PROMPT Executing Customer and Account queries...

-- Query 1: All customers ordered by ID
SELECT * 
FROM TEST_CUSTOMERS 
ORDER BY ID;

-- Query 2: All accounts ordered by Account Number
SELECT * 
FROM TEST_ACCOUNTS 
ORDER BY ACCOUNT_NO;

SELECT  t.FULL_NAME,t.BALANCE
FROM TEST_CUSTOMERS t
where t.id >5 
;

