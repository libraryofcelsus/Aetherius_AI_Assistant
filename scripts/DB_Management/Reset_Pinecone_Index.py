import pinecone


def Reset_Pinecone_Index():
    while True:
        print('Type [Reset Index] to reset the Pinecone Index.')
        print('Please wait 1-2 minutes after reset to allow the index to be created.') 
        try:
            pinecone.describe_index("aetherius")
            a = input(f'\n\nUSER: ')
            if a == 'Reset Index':
                while True:
                    print("\n\nSYSTEM: Are you sure you would like to reset the Pinecone Index?\n        This will result in a complete deletion of Aetherius's memories\n        Press Y for yes or N for no.")
                    user_input = input("'Y' or 'N': ")
                    if user_input == 'y':
                        pinecone.delete_index("aetherius")
                        while True:
                            pinecone.create_index("aetherius", dimension=1536, metric="cosine", pod_type="p1.x1")
                            print('Database has been Reset')
                            return
                    elif user_input == 'n':
                        print('\n\nSYSTEM: Reset cancelled.')
                        return
                else:
                    pass
        except:
            print('No Index named aetherius Detected, creating one now.')
            pinecone.create_index("aetherius", dimension=1536, metric="cosine", pod_type="p1.x1")
            return