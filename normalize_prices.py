import pandas as pd
import numpy as np
from pint import UnitRegistry
import pint
import time

ureg = UnitRegistry()
Q_ = ureg.Quantity

def cost_per_gram(df):
    price_per_gram = []
    for index, row in df.iterrows():
        mass = row['mass']
        price = row['price']

        # default to not having a price/gram
        normalized_price = np.nan

        try:
            # these are the only real errors being checked for
            mass = Q_(mass)
            mass = mass.to(ureg.g)

            normalized_mass = 1 / mass.magnitude
            normalized_price = price * normalized_mass

            #print (f"${normalized_price} per {normalized_mass}")

        except AttributeError as e:
            #print (f'incompatible mass format for {row["ingredient"]}')
            pass
            
        # checks for np.nan values
        except pint.errors.DimensionalityError as e:
            #print (f'no mass for {row["ingredient"]}')
            pass

        price_per_gram.append(normalized_price)

    df['cost_per_gram'] = price_per_gram
    return df

def cost_per_ml(df):
    price_per_ml = []
    for index, row in df.iterrows():
        volume = row['volume']
        price = row['price']

        normalized_price = np.nan

        try:
            # these are the only real errors being checked for
            volume = Q_(volume)
            volume = volume.to(ureg.ml)

            normalized_volume = 1 / volume.magnitude
            normalized_price = price * normalized_volume

            #print (f"${normalized_price} per {normalized_volume}")

        except AttributeError as e:
            #print (f'incompatible volume format for {row["ingredient"]}')
            pass

        # checks for np.nan values
        except pint.errors.DimensionalityError as e:
            #print (f'no volume for {row["ingredient"]}')
            pass

        price_per_ml.append(normalized_price)

    df['cost_per_ml'] = price_per_ml
    return df

def cost_per_s_unit(df):
    price_per_s_units = []
    s_units = []

    for index, row in df.iterrows():
        price = row['price']

        normalized_price = np.nan
        s_unit = np.nan

        try:
            s_number, s_unit = row['s_unit'].split(' ')

            normalized_s_number = 1 / float(s_number)
            normalized_price = price * normalized_s_number
            #print (f'{normalized_price} per {s_unit} {row["ingredient"]}')

        except AttributeError as e:
            #print (f"no special unit for {row['ingredient']}")
            pass

        price_per_s_units.append(normalized_price)
        s_units.append(s_unit)

    df['cost_per_s_unit'] = price_per_s_units
    df['special_unit'] = s_units
    return df

def check_conversions(df):
    for index, row in df.iterrows():
        price = row['price']

        conversions = []

        if pd.notnull(row['cost_per_gram']):
            original_mass = (Q_(row['mass'])).to(ureg.g)
            mass = (row['cost_per_gram']) * original_mass.magnitude
            conversions.append(round(mass, 2))

        if pd.notnull(row['cost_per_ml']):
            original_volume = (Q_(row['volume'])).to(ureg.ml)
            volume = (row['cost_per_ml']) * original_volume.magnitude
            conversions.append(round(volume, 2))

        if pd.notnull(row['cost_per_s_unit']):
            original_s_number = float(row['s_unit'].split(' ')[0])
            s_number = row['cost_per_s_unit'] * original_s_number
            conversions.append(round(s_number, 2))

        for i in range(len(conversions)):
            if i == (len(conversions) - 1):
                pass
            else:
                if abs(conversions[i] - conversions[i + 1]) > .1:
                    print (f'error with {row["ingredient"]}')
                    print (f'{row["ingredient"]}\n{conversions}')


def main():
    master_costs = 'master_costs.csv'
    df_costs = pd.read_csv(master_costs)

    df_costs = cost_per_gram(df_costs)
    df_costs = cost_per_ml(df_costs)
    df_costs = cost_per_s_unit(df_costs)

    check_conversions(df_costs)

    df_finished = df_costs[['ingredient',
                            'cost_per_gram',
                            'cost_per_ml',
                            'cost_per_s_unit',
                            'special_unit',
                            'notes']]

    df_finished.to_csv('normalized_costs.csv', index=False)

if __name__ == '__main__':
    main()
