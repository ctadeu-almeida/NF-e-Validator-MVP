# -*- coding: utf-8 -*-
"""
Chart Generator Module

This module provides comprehensive data visualization capabilities for EDA analysis.
Generates various types of charts and graphs based on data analysis needs.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Optional, Tuple, Any
import warnings
warnings.filterwarnings('ignore')

# Set style for matplotlib
try:
    plt.style.use('seaborn-v0_8')
except OSError:
    try:
        plt.style.use('seaborn')
    except OSError:
        plt.style.use('default')

try:
    sns.set_palette("husl")
except:
    pass  # Use default palette if there's an issue

class ChartGenerator:
    """
    Comprehensive chart generation class for exploratory data analysis
    """

    def __init__(self, data: pd.DataFrame, output_dir: str = "charts"):
        """
        Initialize chart generator

        Args:
            data (pd.DataFrame): The dataset to visualize
            output_dir (str): Directory to save charts
        """
        self.data = data
        self.output_dir = output_dir
        self.numeric_cols = list(data.select_dtypes(include=[np.number]).columns)
        self.categorical_cols = list(data.select_dtypes(include=['object', 'category']).columns)

    def create_data_overview_dashboard(self) -> str:
        """
        Create a comprehensive overview dashboard

        Returns:
            str: Path to saved dashboard
        """
        fig = plt.figure(figsize=(20, 15))

        # Dataset info
        ax1 = plt.subplot(3, 4, 1)
        info_text = f"""
        Dataset Overview:
        • Rows: {self.data.shape[0]:,}
        • Columns: {self.data.shape[1]}
        • Numeric cols: {len(self.numeric_cols)}
        • Categorical cols: {len(self.categorical_cols)}
        • Missing values: {self.data.isnull().sum().sum()}
        """
        ax1.text(0.1, 0.5, info_text, fontsize=12, verticalalignment='center')
        ax1.set_title('Dataset Information', fontsize=14, fontweight='bold')
        ax1.axis('off')

        # Missing values heatmap
        if self.data.isnull().sum().sum() > 0:
            ax2 = plt.subplot(3, 4, 2)
            missing_data = self.data.isnull().sum()
            missing_data = missing_data[missing_data > 0]
            if len(missing_data) > 0:
                missing_data.plot(kind='bar', ax=ax2)
                ax2.set_title('Missing Values by Column')
                ax2.tick_params(axis='x', rotation=45)

        # Data types distribution
        ax3 = plt.subplot(3, 4, 3)
        dtype_counts = self.data.dtypes.value_counts()
        dtype_counts.plot(kind='pie', ax=ax3, autopct='%1.1f%%')
        ax3.set_title('Data Types Distribution')

        # Correlation heatmap for numeric columns
        if len(self.numeric_cols) > 1:
            ax4 = plt.subplot(3, 4, 4)
            corr_matrix = self.data[self.numeric_cols].corr()
            sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', ax=ax4,
                       square=True, cbar_kws={'shrink': 0.8})
            ax4.set_title('Correlation Matrix')

        # Distribution plots for first 4 numeric columns
        for i, col in enumerate(self.numeric_cols[:4]):
            ax = plt.subplot(3, 4, 5 + i)
            self.data[col].hist(bins=30, ax=ax, alpha=0.7)
            ax.set_title(f'Distribution: {col}')
            ax.set_xlabel(col)
            ax.set_ylabel('Frequency')

        # Box plots for outlier detection
        for i, col in enumerate(self.numeric_cols[:4]):
            ax = plt.subplot(3, 4, 9 + i)
            self.data.boxplot(column=col, ax=ax)
            ax.set_title(f'Outliers: {col}')

        plt.tight_layout()
        output_path = f"{self.output_dir}/data_overview_dashboard.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        return output_path

    def create_distribution_plots(self, columns: List[str] = None) -> List[str]:
        """
        Create distribution plots for specified columns

        Args:
            columns: List of column names to plot

        Returns:
            List of paths to saved plots
        """
        if columns is None:
            columns = self.numeric_cols[:6]  # Limit to first 6 columns

        saved_plots = []

        for col in columns:
            if col in self.data.columns:
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

                # Histogram
                self.data[col].hist(bins=30, ax=ax1, alpha=0.7, edgecolor='black')
                ax1.set_title(f'Histogram: {col}')
                ax1.set_xlabel(col)
                ax1.set_ylabel('Frequency')

                # Box plot
                self.data.boxplot(column=col, ax=ax2)
                ax2.set_title(f'Box Plot: {col}')

                plt.tight_layout()
                output_path = f"{self.output_dir}/distribution_{col}.png"
                plt.savefig(output_path, dpi=300, bbox_inches='tight')
                plt.close()
                saved_plots.append(output_path)

        return saved_plots

    def create_correlation_analysis(self) -> str:
        """
        Create comprehensive correlation analysis

        Returns:
            str: Path to saved correlation plot
        """
        if len(self.numeric_cols) < 2:
            return "Insufficient numeric columns for correlation analysis"

        fig, axes = plt.subplots(2, 2, figsize=(20, 16))

        # Correlation heatmap
        corr_matrix = self.data[self.numeric_cols].corr()
        sns.heatmap(corr_matrix, annot=True, cmap='RdBu_r', center=0,
                   square=True, ax=axes[0,0], cbar_kws={'shrink': 0.8})
        axes[0,0].set_title('Correlation Heatmap', fontsize=14, fontweight='bold')

        # Clustermap
        if len(self.numeric_cols) > 3:
            sns.clustermap(corr_matrix, annot=True, cmap='RdBu_r', center=0,
                          square=True, figsize=(12, 10))
            plt.savefig(f"{self.output_dir}/correlation_clustermap.png", dpi=300, bbox_inches='tight')
            plt.close()

        # Strong correlations
        strong_corr = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                corr_val = corr_matrix.iloc[i, j]
                if abs(corr_val) > 0.5:
                    strong_corr.append((corr_matrix.columns[i], corr_matrix.columns[j], corr_val))

        # Plot strongest correlations
        if strong_corr:
            top_corr = sorted(strong_corr, key=lambda x: abs(x[2]), reverse=True)[:5]
            for idx, (col1, col2, corr_val) in enumerate(top_corr[:2]):
                ax = axes[0, 1] if idx == 0 else axes[1, 0]
                self.data.plot.scatter(x=col1, y=col2, ax=ax, alpha=0.6)
                ax.set_title(f'{col1} vs {col2}\nCorrelation: {corr_val:.3f}')

        # Correlation summary text
        axes[1,1].axis('off')
        summary_text = f"""
        Correlation Analysis Summary:

        Total numeric columns: {len(self.numeric_cols)}
        Strong correlations (|r| > 0.5): {len(strong_corr)}

        Strongest correlations:
        """

        if strong_corr:
            for col1, col2, corr_val in sorted(strong_corr, key=lambda x: abs(x[2]), reverse=True)[:5]:
                summary_text += f"• {col1} ↔ {col2}: {corr_val:.3f}\n"
        else:
            summary_text += "• No strong correlations found"

        axes[1,1].text(0.1, 0.7, summary_text, fontsize=12, verticalalignment='top')

        plt.tight_layout()
        output_path = f"{self.output_dir}/correlation_analysis.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        return output_path

    def create_outlier_analysis(self) -> str:
        """
        Create comprehensive outlier analysis

        Returns:
            str: Path to saved outlier analysis plot
        """
        if len(self.numeric_cols) == 0:
            return "No numeric columns for outlier analysis"

        # Calculate number of plots needed
        n_cols = len(self.numeric_cols)
        n_rows = (n_cols + 2) // 3

        fig, axes = plt.subplots(n_rows, 3, figsize=(18, 6*n_rows))
        if n_rows == 1:
            axes = axes.reshape(1, -1)

        outlier_summary = {}

        for idx, col in enumerate(self.numeric_cols):
            row = idx // 3
            col_idx = idx % 3
            ax = axes[row, col_idx]

            # Calculate outliers using IQR method
            Q1 = self.data[col].quantile(0.25)
            Q3 = self.data[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR

            outliers = self.data[(self.data[col] < lower_bound) | (self.data[col] > upper_bound)]
            outlier_count = len(outliers)
            outlier_percentage = (outlier_count / len(self.data)) * 100

            outlier_summary[col] = {
                'count': outlier_count,
                'percentage': outlier_percentage,
                'lower_bound': lower_bound,
                'upper_bound': upper_bound
            }

            # Box plot with outlier highlighting
            box_plot = ax.boxplot(self.data[col], patch_artist=True)
            box_plot['boxes'][0].set_facecolor('lightblue')
            ax.set_title(f'{col}\nOutliers: {outlier_count} ({outlier_percentage:.1f}%)')
            ax.set_ylabel('Value')

        # Remove empty subplots
        for idx in range(n_cols, n_rows * 3):
            row = idx // 3
            col_idx = idx % 3
            fig.delaxes(axes[row, col_idx])

        plt.tight_layout()
        output_path = f"{self.output_dir}/outlier_analysis.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        # Create outlier summary plot
        fig, ax = plt.subplots(figsize=(12, 8))
        columns = list(outlier_summary.keys())
        percentages = [outlier_summary[col]['percentage'] for col in columns]

        bars = ax.bar(columns, percentages, color='coral', alpha=0.7)
        ax.set_title('Outlier Percentage by Column', fontsize=14, fontweight='bold')
        ax.set_xlabel('Columns')
        ax.set_ylabel('Outlier Percentage (%)')
        ax.tick_params(axis='x', rotation=45)

        # Add percentage labels on bars
        for bar, percentage in zip(bars, percentages):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                   f'{percentage:.1f}%', ha='center', va='bottom')

        plt.tight_layout()
        summary_path = f"{self.output_dir}/outlier_summary.png"
        plt.savefig(summary_path, dpi=300, bbox_inches='tight')
        plt.close()

        return output_path

    def create_categorical_analysis(self) -> List[str]:
        """
        Create analysis plots for categorical data

        Returns:
            List of paths to saved plots
        """
        if len(self.categorical_cols) == 0:
            return ["No categorical columns found"]

        saved_plots = []

        for col in self.categorical_cols:
            fig, axes = plt.subplots(1, 2, figsize=(15, 6))

            # Value counts bar plot
            value_counts = self.data[col].value_counts().head(10)
            value_counts.plot(kind='bar', ax=axes[0])
            axes[0].set_title(f'Top 10 Values: {col}')
            axes[0].set_xlabel('Categories')
            axes[0].set_ylabel('Count')
            axes[0].tick_params(axis='x', rotation=45)

            # Pie chart for top categories
            if len(value_counts) <= 8:
                value_counts.plot(kind='pie', ax=axes[1], autopct='%1.1f%%')
                axes[1].set_title(f'Distribution: {col}')
                axes[1].set_ylabel('')

            plt.tight_layout()
            output_path = f"{self.output_dir}/categorical_{col}.png"
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            saved_plots.append(output_path)

        return saved_plots

    def create_time_series_analysis(self, time_col: str = 'Time') -> str:
        """
        Create time series analysis if time column exists

        Args:
            time_col: Name of the time column

        Returns:
            str: Path to saved time series plot
        """
        if time_col not in self.data.columns:
            return f"Time column '{time_col}' not found"

        fig, axes = plt.subplots(2, 2, figsize=(16, 12))

        # Time distribution
        axes[0,0].hist(self.data[time_col], bins=50, alpha=0.7)
        axes[0,0].set_title('Time Distribution')
        axes[0,0].set_xlabel('Time (seconds)')
        axes[0,0].set_ylabel('Frequency')

        # Transaction frequency over time
        time_bins = pd.cut(self.data[time_col], bins=50)
        time_counts = time_bins.value_counts().sort_index()
        axes[0,1].plot(range(len(time_counts)), time_counts.values)
        axes[0,1].set_title('Transaction Frequency Over Time')
        axes[0,1].set_xlabel('Time Bins')
        axes[0,1].set_ylabel('Transaction Count')

        # Time differences
        time_diff = self.data[time_col].diff().dropna()
        axes[1,0].hist(time_diff, bins=50, alpha=0.7)
        axes[1,0].set_title('Time Differences Between Transactions')
        axes[1,0].set_xlabel('Time Difference (seconds)')
        axes[1,0].set_ylabel('Frequency')

        # Summary statistics
        axes[1,1].axis('off')
        summary_text = f"""
        Time Analysis Summary:

        • Total time span: {self.data[time_col].max() - self.data[time_col].min():.0f} seconds
        • Average time between transactions: {time_diff.mean():.2f} seconds
        • Median time between transactions: {time_diff.median():.2f} seconds
        • Min time difference: {time_diff.min():.2f} seconds
        • Max time difference: {time_diff.max():.2f} seconds
        • Total transactions: {len(self.data):,}
        """
        axes[1,1].text(0.1, 0.8, summary_text, fontsize=12, verticalalignment='top')

        plt.tight_layout()
        output_path = f"{self.output_dir}/time_series_analysis.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        return output_path

    def create_pca_analysis_plot(self, pca_columns: List[str] = None) -> str:
        """
        Create analysis plots for PCA-transformed columns (V1-V28)

        Args:
            pca_columns: List of PCA column names

        Returns:
            str: Path to saved PCA analysis plot
        """
        if pca_columns is None:
            pca_columns = [col for col in self.data.columns if col.startswith('V') and col[1:].isdigit()]

        if len(pca_columns) == 0:
            return "No PCA columns found"

        fig, axes = plt.subplots(2, 2, figsize=(16, 12))

        # PCA components variance
        pca_data = self.data[pca_columns]
        variances = pca_data.var().sort_values(ascending=False)

        axes[0,0].bar(range(len(variances[:10])), variances[:10])
        axes[0,0].set_title('Top 10 PCA Components by Variance')
        axes[0,0].set_xlabel('PCA Components')
        axes[0,0].set_ylabel('Variance')
        axes[0,0].set_xticks(range(len(variances[:10])))
        axes[0,0].set_xticklabels(variances[:10].index, rotation=45)

        # PCA components correlation with target (if Class exists)
        if 'Class' in self.data.columns:
            correlations = []
            for col in pca_columns:
                corr = self.data[col].corr(self.data['Class'])
                correlations.append((col, abs(corr)))

            correlations.sort(key=lambda x: x[1], reverse=True)
            top_corr = correlations[:10]

            axes[0,1].bar(range(len(top_corr)), [x[1] for x in top_corr])
            axes[0,1].set_title('Top 10 PCA Components Correlation with Class')
            axes[0,1].set_xlabel('PCA Components')
            axes[0,1].set_ylabel('|Correlation|')
            axes[0,1].set_xticks(range(len(top_corr)))
            axes[0,1].set_xticklabels([x[0] for x in top_corr], rotation=45)

        # Cumulative variance explained (approximation)
        cumvar = variances.cumsum() / variances.sum()
        axes[1,0].plot(range(1, len(cumvar[:20])+1), cumvar[:20])
        axes[1,0].set_title('Cumulative Variance Explained (First 20 Components)')
        axes[1,0].set_xlabel('Number of Components')
        axes[1,0].set_ylabel('Cumulative Variance Ratio')
        axes[1,0].grid(True)

        # PCA summary statistics
        axes[1,1].axis('off')
        summary_text = f"""
        PCA Analysis Summary:

        • Total PCA components: {len(pca_columns)}
        • Highest variance component: {variances.index[0]}
        • Highest variance value: {variances.iloc[0]:.4f}
        • Mean component variance: {variances.mean():.4f}
        • Total variance: {variances.sum():.2f}
        """

        if 'Class' in self.data.columns:
            summary_text += f"\n• Highest correlation with Class: {correlations[0][0]}"
            summary_text += f"\n• Correlation value: {correlations[0][1]:.4f}"

        axes[1,1].text(0.1, 0.8, summary_text, fontsize=12, verticalalignment='top')

        plt.tight_layout()
        output_path = f"{self.output_dir}/pca_analysis.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        return output_path

    def create_custom_plot(self, plot_type: str, x_col: str = None, y_col: str = None, **kwargs) -> str:
        """
        Create custom plots based on user specifications

        Args:
            plot_type: Type of plot ('scatter', 'line', 'bar', 'hist', 'box')
            x_col: X-axis column name
            y_col: Y-axis column name
            **kwargs: Additional plot parameters

        Returns:
            str: Path to saved custom plot
        """
        fig, ax = plt.subplots(figsize=(12, 8))

        if plot_type == 'scatter' and x_col and y_col:
            self.data.plot.scatter(x=x_col, y=y_col, ax=ax, alpha=0.6)
            ax.set_title(f'Scatter Plot: {x_col} vs {y_col}')

        elif plot_type == 'hist' and x_col:
            self.data[x_col].hist(bins=kwargs.get('bins', 30), ax=ax, alpha=0.7)
            ax.set_title(f'Histogram: {x_col}')

        elif plot_type == 'box' and x_col:
            self.data.boxplot(column=x_col, ax=ax)
            ax.set_title(f'Box Plot: {x_col}')

        elif plot_type == 'line' and x_col and y_col:
            self.data.plot.line(x=x_col, y=y_col, ax=ax)
            ax.set_title(f'Line Plot: {x_col} vs {y_col}')

        plt.tight_layout()
        output_path = f"{self.output_dir}/custom_{plot_type}_{x_col or 'plot'}.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        return output_path

    def generate_comprehensive_report(self) -> Dict[str, str]:
        """
        Generate a comprehensive visualization report

        Returns:
            Dict with paths to all generated charts
        """
        import os
        os.makedirs(self.output_dir, exist_ok=True)

        report = {}

        # Generate all available visualizations
        report['overview_dashboard'] = self.create_data_overview_dashboard()
        report['correlation_analysis'] = self.create_correlation_analysis()
        report['outlier_analysis'] = self.create_outlier_analysis()

        if self.categorical_cols:
            report['categorical_analysis'] = self.create_categorical_analysis()

        if 'Time' in self.data.columns:
            report['time_series_analysis'] = self.create_time_series_analysis()

        # Check for PCA columns
        pca_cols = [col for col in self.data.columns if col.startswith('V') and col[1:].isdigit()]
        if pca_cols:
            report['pca_analysis'] = self.create_pca_analysis_plot(pca_cols)

        return report