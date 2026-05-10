from pathlib import Path
from math import erf, sqrt

import matplotlib.pyplot as plt
import pandas as pd


DATA_PATH = Path('orders.csv')
FIGURES_DIR = Path('figures')


def normal_cdf(x):
    return 0.5 * (1 + erf(x / sqrt(2)))


def conversion_z_test(success_a, total_a, success_b, total_b):
    conversion_a = success_a / total_a
    conversion_b = success_b / total_b
    pooled = (success_a + success_b) / (total_a + total_b)
    standard_error = sqrt(pooled * (1 - pooled) * (1 / total_a + 1 / total_b))
    z_score = (conversion_b - conversion_a) / standard_error
    p_value = 2 * (1 - normal_cdf(abs(z_score)))
    return conversion_a, conversion_b, z_score, p_value


def main():
    orders = pd.read_csv(DATA_PATH)
    orders['order_date'] = pd.to_datetime(orders['order_date'])
    orders['revenue'] = pd.to_numeric(orders['revenue'])

    paid_orders = orders[orders['ordered'] == 1].copy()

    total_revenue = paid_orders['revenue'].sum()
    orders_count = paid_orders['order_id'].count()
    average_order_value = paid_orders['revenue'].mean()

    print('Основные метрики')
    print(f'Выручка: {total_revenue:.2f}')
    print(f'Количество заказов: {orders_count}')
    print(f'Средний чек: {average_order_value:.2f}')
    print()

    revenue_by_day = paid_orders.groupby('order_date', as_index=False)['revenue'].sum()
    category_stats = (
        paid_orders.groupby('category', as_index=False)
        .agg(orders=('order_id', 'count'), revenue=('revenue', 'sum'))
        .sort_values('revenue', ascending=False)
    )

    print('Продажи по категориям')
    print(category_stats.to_string(index=False))
    print()

    ab_data = orders.groupby('group').agg(
        visitors=('visited', 'sum'),
        orders=('ordered', 'sum')
    )

    conversion_a, conversion_b, z_score, p_value = conversion_z_test(
        ab_data.loc['A', 'orders'],
        ab_data.loc['A', 'visitors'],
        ab_data.loc['B', 'orders'],
        ab_data.loc['B', 'visitors']
    )

    print('A/B-тест по конверсии')
    print(f'Группа A: {conversion_a:.2%}')
    print(f'Группа B: {conversion_b:.2%}')
    print(f'z-score: {z_score:.3f}')
    print(f'p-value: {p_value:.3f}')

    if p_value < 0.05:
        print('Разница статистически значима на уровне 5%')
    else:
        print('Статистически значимой разницы на уровне 5% нет')

    FIGURES_DIR.mkdir(exist_ok=True)

    plt.figure(figsize=(9, 5))
    plt.plot(revenue_by_day['order_date'], revenue_by_day['revenue'], marker='o')
    plt.title('Выручка по дням')
    plt.xlabel('Дата')
    plt.ylabel('Выручка')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / 'revenue_by_day.png')
    plt.close()

    plt.figure(figsize=(8, 5))
    plt.bar(category_stats['category'], category_stats['revenue'])
    plt.title('Выручка по категориям')
    plt.xlabel('Категория')
    plt.ylabel('Выручка')
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / 'revenue_by_category.png')
    plt.close()


if __name__ == '__main__':
    main()
