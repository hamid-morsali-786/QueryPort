-- ======================================================================
-- TEST SCRIPT 2: 02_TRANSACTIONS_AND_BRANCHES.sql
-- Contains 2 SELECT queries for Transactions and Branches
-- ======================================================================

PROMPT Executing Transactions and Branches queries...

-- Query 1: All transactions ordered by Txn ID
SELECT * 
FROM TEST_TRANSACTIONS 
ORDER BY TXN_ID;

-- Query 2: Active and inactive branches ordered by Branch Code
SELECT * 
FROM TEST_BRANCHES 
ORDER BY BRANCH_CODE;
