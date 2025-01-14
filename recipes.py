import pandas as pd
import numpy as np

class RecipeHandler:
    def __init__(self):
        self.recipes_df = pd.read_csv('recipes.csv')
    
    @staticmethod
    def convert_time_to_minutes(time_str):
        if isinstance(time_str, float):
            return time_str

        parts = time_str.split(' ')
        total_minutes = 0
        for i in range(0, len(parts), 2):
            value = int(parts[i])
            unit = parts[i + 1].lower()
            if 'day' in unit:
                total_minutes += value * 24 * 60
            elif 'hr' in unit:  # Check for 'hr' or 'hrs'
                total_minutes += value * 60
            elif 'min' in unit:  # Check for 'min' or 'mins'
                total_minutes += value
        return total_minutes
    
    def recommend_recipes(self, target_cooking_time):
        df = self.recipes_df.dropna(subset=['total_time'])
        df['total_time'] = df['total_time'].apply(self.convert_time_to_minutes)
        df = df[df['total_time'] <= 150]
        time_diffs = abs(df['total_time'] - (target_cooking_time / 2))
        top_indices = time_diffs.argsort()[:15].reset_index(drop = True)
        # print(top_indices)
        shuffled_indices = np.array(top_indices)
        np.random.shuffle(shuffled_indices)
        #np.random.shuffle(top_indices)
        recommended_recipes = df.iloc[shuffled_indices][:1]
        return recommended_recipes[['recipe_name', 'total_time', 'url']]
    
    def main(self):
        sche = pd.read_csv("saved_rn.csv")
        sche["Duration"] = sche["Duration"].str.extract(r'(\d)').astype(int) * 60
        recipe_list = [self.recommend_recipes(value) for value in sche['Duration']]
        combined_df = pd.concat(recipe_list, ignore_index=True)
        concatenated_df = pd.concat([sche, combined_df], axis=1)
        concatenated_df.to_csv('recipeRec.csv')
        return concatenated_df
        
# if __name__ == "__main__":
#     handler = RecipeHandler('recipes.csv')
#     handler.main('freetimes.csv', 'recipeRec.csv')
