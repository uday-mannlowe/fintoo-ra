-- migrate_chatbot_tables.sql
-- ✅ NO ACTION NEEDED
-- Your database already has the chatbot_interactions table with all required columns:
--
--   interaction_id    uuid  PK
--   user_id           uuid  FK → users
--   interaction_type  varchar   (income_update / loan_add / general_query / etc.)
--   question_asked    text      (user's message)
--   user_response     text      (assistant's reply)
--   detected_change   jsonb     (full intent JSON from Groq)
--   was_confirmed     boolean   (NULL=pending, TRUE=confirmed, FALSE=cancelled)
--   led_to_update     boolean   (TRUE if DB was changed)
--   created_at        timestamptz
--
-- The chatbot uses interaction_id as the session_id.
-- No new tables required.

SELECT 'chatbot_interactions table already exists - no migration needed.' AS status;
