        # # Generate Semantic Search Terms
        master_tasklist.append({'role': 'system', 'content': "You are a task list coordinator. Your job is to take user input and create a list of inquiries to be used for orchestrating Ai agents. Use the format [- '____']."})
        master_tasklist.append({'role': 'user', 'content': "Do you understand your imperatives?"})
        master_tasklist.append({'role': 'assistant', 'content': "-Agent should research its own imperatives.\n-Agent should confirm to user it's understanding."})
        master_tasklist.append({'role': 'user', 'content': "%s" % a})
        master_tasklist_output = chatgpt200_completion(tasklist)
        tasklist_completion.append({'role': 'system', 'content': "You are the final execution module for an Ai chatbot. Your job is to take a completed task list, then format it for the end user in accordance with their initial request."})
        tasklist_completion.append({'role': 'user', 'content': "%s" % master_tasklist_output})
        task = {}
        task_result = {}
        task_result2 = {}
        task_counter = 0
        # # Split bullet points into separate lines to be used as individual queries
        lines = tasklist_output.splitlines()
        for line in lines:
            if line.strip():
                tasklist_completion.append({'role': 'user', 'content': "ASSIGNED TASK:\n%s" % line})
                print(line)
                task_vector = gpt3_embedding(line)
                task_counter += 1
                task[task_counter] = task_vector
                results = vdb.query(vector=task[task_counter], top_k=3, namespace='heuristics')
                task_result[task_counter] = load_conversation_heuristics(results)
                results = vdb.query(vector=task[task_counter], top_k=2, namespace='long_term_memory')
                task_result2[task_counter] = load_conversation_long_term_memory(results)
                conversation.append({'role': 'system', 'content': "You are a sub-module for an Autonomous Ai-Chatbot. You are one of many agents in a chain. You are to take the given task and complete it in its entirety. Take future tasks into account when formulating your answer."})
                conversation.append({'role': 'user', 'content': "Task list:\n%s" % master_tasklist_output})
                conversation.append({'role': 'assistant', 'content': "I have studied the given tasklist.  What is my assigned task?"})
                conversation.append({'role': 'user', 'content': "Your assigned task: %s" % task_result[task_counter]})
                conversation.append({'role': 'assistant', 'content': "Understood, I will now complete my given task in its entirety:"})
                task_completion = chatgptresponse_completion(conversation)
                tasklist_completion.append({'role': 'assistant', 'content': "COMPLETED TASK:\n%s" % task_completion})
                # # Stop updating conversation list for intuition loop to avoid token limit
                    
                    
                    
                    
        tasklist_completion.append({'role': 'user', 'content': "Take the given set of tasks and responses and format them into a final response to the user's initial inquiry.  User's initial inquiry: %s" % a})
