from RhythmTyperAPI.client import RhythmTyperClient
import json, os

rt = RhythmTyperClient()

json_file_path = "./bn-list.json"
usernames = ["Aniviuh", "Cardboard_Dragon", "extra", "FiXsy", "goink", "Knight", "olc", "Riguren", "Yomia", "zabrid", "Piger"]


def main():
    cls()
    print("Wait while we fetch the nomination data...\n")
    
    update_json(json_file_path, usernames)
    nominators = get_nomination_data(json_file_path)
    
    while True:
        cls()
        
        print("Welcome to the RhythmTyper BN Nomination Tracker!\n")
        print("1. Display all profiles summary")
        print("2. Display only recently nominated maps (last 90 days)")
        print("3. Display all nominated maps")
        print("4. Exit\n")
        
        choice = input("Enter your choice: ")
        
        if choice == "1":
            display_all_profiles_summary(nominators)
            input("\nPress Enter to return to the main menu...")
        elif choice == "2":
            display_nominated_maps(nominators, isRecent=True)
            input("\nPress Enter to return to the main menu...")
        elif choice == "3":
            display_nominated_maps(nominators, isRecent=False)
            input("\nPress Enter to return to the main menu...")
        elif choice == "4":
            break
        else:
            print("Invalid choice. Please try again.")
            input("\nPress Enter to return to the main menu...")
    

def display_all_profiles_summary(nominators):
    cls()
    
    for profile in nominators:
        print(f"{profile['username']} ({profile['role']}) [{profile['days_remaining']} days remaining]:\n{profile['recent_maps_count']} recently nominated maps out of {profile['maps_count']} total.\n")


def display_nominated_maps(nominators, isRecent: bool = False):
    number_of_profiles = len(nominators)
    
    for i, profile in enumerate(nominators):
        if isRecent:
            maps = profile['recent_maps']
            maps_count = profile['recent_maps_count']
        else:
            maps = profile['maps']
            maps_count = profile['maps_count']
        
        cls()
        
        print(f"\n{profile['username']} ({profile['role']}) has {maps_count} nominated maps{f' ({profile['days_remaining']} days remaining)' if isRecent else ''}:\n")
            
        print('\n'.join(f"{map['title']} - {map['artist']} [{map['mapper']}] ({map['status']})\nNoms: {', '.join([nom['nominatorUsername'] + ' (' + nom['nominatedAt'] + ')' for nom in map['nominations']])}\n" for map in maps))
        
        user_input = input(f"\nPress Enter to continue to the next profile... or type 'exit' to quit: ({i + 1}/{number_of_profiles}) ")
        if user_input.lower() == 'exit':
            break
    

def get_nomination_data(file_path):
    nominators = []
    
    with open(file_path, "r+", encoding='utf-8') as f:
        data = json.load(f)
        profiles = data.get("nominators", [])
    
        for profile in profiles:        
            # if profile doesn't have a userid, look it up and add it to the json file
            if profile.get("userid") == "":
                username = profile.get("username")
                user = rt.user_lookup(username, 1)
                profile["userid"] = user[0].user_id
                f.seek(0)
                json.dump(data, f, indent=4)
        
            maps, maps_count = get_nominated_maps(profile['userid'])
            recent_maps, recent_maps_count = get_only_recently_nominated_maps(maps)
            days_remaining = get_days_remaining(recent_maps, recent_maps_count)
            
            nominators.append({
                "username": profile['username'],
                "role": profile['role'],
                "maps": maps,
                "maps_count": maps_count,
                "recent_maps": recent_maps,
                "recent_maps_count": recent_maps_count,
                "days_remaining": days_remaining
            })
    
    sorted_nominators = sorted(sorted(nominators, key=lambda x: x['recent_maps_count'], reverse=False), key=lambda x: x['days_remaining'], reverse=False)
    
    return sorted_nominators


def get_days_remaining(recent_maps, recent_maps_count):
    if recent_maps_count >= 3:
        if recent_maps[2]['nominated_at'] is not None:
            from datetime import datetime
            from pytz import timezone
            
            nominated_at = datetime.strptime(recent_maps[2]["nominated_at"], "%Y-%m-%dT%H:%M:%S.%fZ")
            return (timezone('utc').localize(datetime.now()) - nominated_at.replace(tzinfo=timezone('utc'))).days
    return 0


def cls():
    os.system('cls' if os.name=='nt' else 'clear')


def get_only_recently_nominated_maps(maps: list, days: int = 90):
    from datetime import datetime, timedelta
    from pytz import timezone
    
    filtered_maps = []
    
    for map in maps:
        if map["nominated_at"] is not None:
            nominated_at = datetime.strptime(map["nominated_at"], "%Y-%m-%dT%H:%M:%S.%fZ")
            if nominated_at.replace(tzinfo=timezone('utc')) >= timezone('utc').localize(datetime.now()) - timedelta(days=days):
                filtered_maps.append(map)
        else:
            continue
    
    return filtered_maps, len(filtered_maps)


def get_nominated_maps(user_id):
    nomination_data = rt.get_nominations(user_id)
    
    maps = []
    
    for map in nomination_data:
        maps.append({
            "title": map.beatmap_title,
            "artist": map.beatmap_artist,
            "mapper": map.mapper,
            "ranked": map.ranked,
            "status": map.status,
            "nomination_count": map.nomination_count,
            "nominations": map.nominations,
            "ranked_date": map.ranked_date,
            "qualified_date": map.qualified_date,
            "nominated_at": map.nominated_at
        })
    
    return maps, len(maps)

            
def update_json(file_path, usernames=None):
    # Check if file exists
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = json.load(file)
                if "nominators" not in content:
                    content["nominators"] = []
        except json.JSONDecodeError:
            print(f"Warning: {file_path} contains invalid JSON. Creating new file with default content.")
            content = {"nominators": []}
    else:
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        content = {"nominators": []}
    
    # If no usernames provided, just ensure file exists and return
    if usernames is None:
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(content, file, indent=4, ensure_ascii=False)
        return content
    
    usernames_set = set(usernames)
    
    # Filter existing users: keep only those in the new list
    kept_users = []
    removed_users = []
    
    for entry in content["nominators"]:
        if entry["username"] in usernames_set:
            kept_users.append(entry)
        else:
            removed_users.append(entry["username"])
    
    # Add new users that don't already exist
    existing_usernames = {entry["username"] for entry in kept_users}
    added_users = []
    
    for username in usernames:
        if username not in existing_usernames:
            kept_users.append({
                "username": username,
                "userid": "",
                "role": "BN"
            })
            added_users.append(username)
            existing_usernames.add(username)
    
    # Update content
    content["nominators"] = kept_users
    
    # Write back to file
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(content, file, indent=4, ensure_ascii=False)
    
    # Print summary
    if removed_users:
        print(f"Removed users ({len(removed_users)}): {', '.join(removed_users)}")
    if added_users:
        print(f"Added users ({len(added_users)}): {', '.join(added_users)}")
    if not removed_users and not added_users:
        print("No changes made to the nominators list.")


if __name__ == "__main__":
    main()