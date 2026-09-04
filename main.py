from RhythmTyperAPI.client import RhythmTyperClient
import json, os

rt = RhythmTyperClient()

json_file_path = "./bn-list.json"
usernames = ["Aniviuh", "Cardboard_Dragon", "extra", "FiXsy", "goink", "Knight", "olc", "Riguren", "Yomia", "zabrid", "Piger"]


def main():
    cls()
    print("Wait while we fetch the nomination data...\n")

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


def get_nominators():
    nominators_json = rt.nominators().nominators
    
    nominators = []
    
    for nominator in nominators_json:
        if not nominator.is_nominator or nominator.is_admin: continue
        
        profile = {
            "username": nominator.username,
            "userid": nominator.user_id,
            "role": "NAT" if nominator.is_rank_manager else "BN"
        }
        
        nominators.append(profile)
    
    return nominators
        
        
def get_nomination_data(file_path):
    nominators = []
    
    nominators_list = get_nominators()
    
    for nominator in nominators_list:
        maps, maps_count = get_nominated_maps(nominator['userid'])
        recent_maps, recent_maps_count = get_only_recently_nominated_maps(maps)
        days_remaining = get_days_remaining(recent_maps, recent_maps_count)
        
        nominators.append({
            "username": nominator['username'],
            "role": nominator['role'],
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
            return 90 - (timezone('utc').localize(datetime.now()) - nominated_at.replace(tzinfo=timezone('utc'))).days
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


if __name__ == "__main__":
    main()