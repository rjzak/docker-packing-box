# -*- coding: UTF-8 -*-
from contextlib import suppress
from functools import wraps

from .algorithm import Algorithm 
from ...helpers import *

lazy_load_module("sklearn.tree", alias="sktree")


__all__ = ["VISUALIZATIONS"]


def _preprocess(f):
    """ This decorator preprocesses the input data and updates the keyword-arguments with this fitted data. """
    @wraps(f)
    def _wrapper(*args, **kwargs):
        from sklearn.impute import SimpleImputer
        from sklearn.preprocessing import MinMaxScaler
        X = kwargs['data']
        n_cols = len(X.columns)
        n, p = kwargs.get('n_components', min(20, n_cols)), kwargs.get('perplexity', 30)
        suffix = ""
        X = SimpleImputer(missing_values=np.nan, strategy=kwargs.get('imputer_strategy', "mean")).fit_transform(X)
        X = MinMaxScaler().fit_transform(X)
        # update the keyword-arguments with the scaled data, since it may be used in the visualization ;
        #  do not update the 'data' keyword-argument, since it is used for features visualization
        kwargs['scaled_data'] = X 
        # preprocess data with a PCA with n components to reduce the high dimensionality (better performance)
        if n < n_cols:
            from sklearn.decomposition import FastICA, PCA
            ra = kwargs.get('reduction_algorithm', "PCA")
            a = {'ICA': FastICA, 'PCA': PCA}[ra](n, random_state=42)
            suffix += "_%s%d" % (ra.lower(), n)
            if 'target' in kwargs:
                a.fit(X, kwargs['target'])
                X = a.transform(X)
            else:
                X = a.fit_transform(X)
        # now reduce the n components to 2 dimensions with t-SNE (better results but less performance) if relevant
        if n > 2:
            from sklearn.manifold import TSNE
            X = TSNE(2, random_state=42, perplexity=p).fit_transform(X)
            suffix += "_tsne2-p%d" % p
        kwargs['reduced_data'] = X
        fig = f(*args, **kwargs)
        fig.dst_suffix = suffix
        return fig
    return _wrapper


def _title(algo_name=None, dataset_name=None, n_components=None, perplexity=None, reduction_algorithm=None, **kw):
    dimensionality_reduction_info = ""
    if n_components is not None and reduction_algorithm is not None:
        dimensionality_reduction_info = f"{reduction_algorithm} ({n_components} Components)"
        if reduction_algorithm == "PCA" and n_components > 2:
            dimensionality_reduction_info += f" and t-SNE (2 Components, Perplexity: {perplexity})"
    elif n_components is not None:
        dimensionality_reduction_info = f"Dimensionality Reduction ({n_components} Components)"
    return f"{algo_name} Visualization of dataset {dataset_name} \n with {dimensionality_reduction_info}"

def _add_colorbar(ax, norm, colors):
    fig = ax.get_figure()
    bbox = ax.get_position() # bbox contains the [x0 (left), y0 (bottom), x1 (right), y1 (top)] of the axis.
    width = 0.01
    eps = 0.01 # margin between plot and colorbar
    # [left most position, bottom position, width, height] of color bar
    cax = fig.add_axes([bbox.x1 + eps, bbox.y0, width, bbox.height])
    cbar = fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=colors), cax=cax)

def image_dt(classifier, width=5, fontsize=10, **params):
    params['filled'] = True
    fig = plt.figure()
    sktree.plot_tree(classifier, **params)
    return fig


@_preprocess
def image_knn(classifier, **params):
    from sklearn.inspection import DecisionBoundaryDisplay
    from sklearn.neighbors import KNeighborsClassifier
    X, y = params['data'], params['target']
    # retrain kNN with the preprocessed data (with dimensionality reduced to N=2, hence not using 'classifier')
    knn = KNeighborsClassifier(**params['algo_params'])
    knn.fit(X, y)
    # now set color map then plot
    labels = list(y.label.unique())
    colors = mpl.cm.get_cmap("jet", len(labels))
    fig, axes = plt.subplots()
    DecisionBoundaryDisplay.from_estimator(knn, X, cmap=colors, ax=axes, alpha=.3,
                                           response_method="predict", plot_method="pcolormesh", shading="auto")
    plt.scatter(X[:, 0], X[:, 1], c=[labels.index(v) for v in y.label.ravel()][::-1], cmap=colors, alpha=1.0)
    return fig


def image_rf(classifier, width=5, fontsize=10, **params):
    from math import ceil
    n = len(classifier.estimators_)
    rows = ceil(n / width)
    cols = width if rows > 1 else n
    fig, axes = plt.subplots(nrows=rows, ncols=cols, figsize=tuple(map(lambda x: 2*x, (cols, rows))), dpi=900)
    # flatten axes, otherwise it is a matrix of all subplots
    with suppress(TypeError):
        axes = [ax for lst in axes for ax in lst]
    params['filled'] = True
    for i in range(n):
        sktree.plot_tree(classifier.estimators_[i], ax=axes[i], **params)
        axes[i].set_title("Estimator: %d" % i, fontsize=fontsize)
    return fig


@_preprocess
def image_clustering(classifier, **params):
    from scipy.cluster.hierarchy import linkage, fcluster, dendrogram
    from sklearn.cluster import AgglomerativeClustering
    X, y = params['data'], params['target']
    X_reduced = params['reduced_data']  
    X_scaled = params['scaled_data']      
    # retrain either with the preprocessing data or with the original data
    cls = Algorithm.get(params['algo_name']).base(**params['algo_params'])
    if params.get('reduce_train_data', False):
        label = cls.fit_predict(X_reduced)
    else : 
        label = cls.fit_predict(X_scaled)
    # get labels for hierarchical clustering
    is_hierarchical = isinstance(cls, AgglomerativeClustering)
    if is_hierarchical: 
        if params.get('reduce_train_data', False):
            Z = linkage(X_reduced, method='ward')
        else : 
            Z = linkage(X_scaled, method='average')
        color_threshold = params['distance_threshold']
    # now set color map
    colors = mpl.cm.get_cmap("jet")
    # adjust number of plots and size of figure
    features = params['features'][0]
    n_features = len(features)
    n_plots = int(params['plot_labels']) + int(is_hierarchical) + int(params['plot_extensions']) + \
              int(params['plot_formats']) + n_features + 1
    font_size = 16
    plt.rcParams['axes.labelsize'] = 16
    plt.rcParams['xtick.labelsize'], plt.rcParams['ytick.labelsize'] = 14, 14
    fig, axes = plt.subplots(n_plots ,figsize=(10 , 6 + 3 * n_plots))
    # wrap the AxesSubplot object in a list to make it subscriptable when there is only one plot
    if not isinstance(axes, (list, np.ndarray)):
        axes = [axes]
    current_ax = 0 
    # select zone of data to plot
    if params['range'] is not None:
        if is_hierarchical:
            raise ValueError("Error: Zone selection is not compatible with hierarchical clustering")
        x_min, x_max, y_min, y_max = params['range']
        range_mask = (X_reduced[:, 0] >= x_min) & (X_reduced[:, 0] <= x_max) & (X_reduced[:, 1] >= y_min) & \
                     (X_reduced[:, 1] <= y_max)
        X_reduced = X_reduced[range_mask]
        X = X[range_mask]
        y = y[range_mask]
        label = label[range_mask]
        params['labels'] = params['labels'][range_mask]
        params['extension'] = params['extension'][range_mask]
        params['format'] =  params['format'][range_mask]
        if X_reduced.size == 0 :
            raise ValueError("Error: The selected zone is empty")
    # plot dendrogram for hierarchical clustering
    if is_hierarchical: 
        # dendogram used to get the leaves and colors for the scatter plot since it is not truncated. 
        d = dendrogram(Z, ax=axes[0], no_plot= True, color_threshold=color_threshold, above_threshold_color='k')
        # dendogram that is effectively plotted (truncated)
        dendrogram(Z, ax=axes[0], p=params['hierarchy_levels'], leaf_rotation=90., leaf_font_size=8.,
                   truncate_mode='level', show_contracted=params['hierarchy_levels'] <= 5,
                   color_threshold=color_threshold, above_threshold_color='k')        
        axes[current_ax].set_title("Dendrogram", fontsize=font_size)
        current_ax += 1
    # plot predicted cluster labels
    if is_hierarchical:
        axes[current_ax].scatter(X_reduced[d['leaves'],0],X_reduced[d['leaves'],1], color=d['leaves_color_list'])
    else : 
        predicted_labels = np.unique(label)
        offset = 0
        if -1 in predicted_labels:  # -1 is for outliers in DBSCAN but messes with colors
            offset = 1
        cluster_colors = {i: colors((i + offset) / len(predicted_labels)) for i in predicted_labels} \
                         if not is_hierarchical else cluster_colors
        for i in predicted_labels:
            axes[current_ax].scatter(X_reduced[label == i, 0], X_reduced[label == i, 1] , label=i,
                                     color=cluster_colors[i])
    axes[current_ax].set_title("Clusters", fontsize=font_size)
    current_ax += 1 
    # plot true labels
    if params['plot_labels']:
        if params['multiclass']:
            y_labels = np.unique(params['labels'])
            colors_labels = mpl.cm.get_cmap("jet", len(y_labels))
            label_map = {label: 'Not packed' if label == '-' else f'Packed : {label}' for label in y_labels}
        else : 
            colors_labels = mpl.cm.get_cmap("jet", 2)
            y_labels = np.unique(y.label.ravel())
            label_map = {0: 'Not packed', 1: 'Packed'}
        for i, y_label in enumerate(y_labels):
            labels_mask = params['labels'] == y_label if params['multiclass'] else y.label.ravel() == y_label
            axes[current_ax].scatter(X_reduced[labels_mask, 0], X_reduced[labels_mask, 1],
                            label=label_map[y_label], color=colors_labels(i), alpha=1.0)
        axes[current_ax].legend(loc='upper left', bbox_to_anchor=(1, 1),fontsize=font_size-2)  
        axes[current_ax].set_title("Target", fontsize=font_size)
        current_ax += 1
    # plot file formats
    if params['plot_formats']:
        unique_formats = np.unique(params['format'])
        for file_format in unique_formats:
            format_mask = params['format'] == file_format
            axes[current_ax].scatter(X_reduced[format_mask, 0], X_reduced[format_mask, 1],
                            label=file_format, cmap=colors, alpha=1.0)
        axes[current_ax].legend(loc='upper left', bbox_to_anchor=(1, 1),fontsize=font_size-2)
        axes[current_ax].set_title("File Formats", fontsize=font_size)
        current_ax += 1 
    # plot file extensions
    if params['plot_extensions']:
        unique_extensions = np.unique(params['extension'])
        for file_extension in unique_extensions:
            extension_mask = params['extension'] == file_extension
            axes[current_ax].scatter(X_reduced[extension_mask, 0], X_reduced[extension_mask, 1],
                            label=file_extension, cmap=colors, alpha=1.0)
        axes[current_ax].legend(loc='upper left', bbox_to_anchor=(1, 1),fontsize=font_size-2)
        axes[current_ax].set_title("File Extensions", fontsize=font_size)
        current_ax += 1 
    # plot selected features
    color_bars = {}
    if features :
        for i, feature in enumerate(features) : 
            unique_feature_values = np.unique(X[feature])
            # plot a continuous colorbar if the feature is continuous and a legend otherwise 
            if len(unique_feature_values) > 6:
                sc = axes[current_ax].scatter(X_reduced[:, 0], X_reduced[:, 1], c=X[feature].to_numpy(), cmap=colors,
                                              alpha=1.0)
                norm = mpl.colors.Normalize(vmin=X[feature].min(), vmax=X[feature].max())
                color_bars[current_ax] = norm
            else : 
                for feature_value in unique_feature_values:
                    axes[current_ax].scatter(X_reduced[X[feature] == feature_value, 0],
                                             X_reduced[X[feature] == feature_value, 1],
                                             label=feature_value, cmap=colors, alpha=1.0)
                    axes[current_ax].legend(loc='upper left', bbox_to_anchor=(1, 1),fontsize=font_size-2)  
            axes[current_ax].set_title(feature, fontsize=font_size)
            current_ax += 1 
    title = _title(**params)
    plt.suptitle(title, fontweight="bold", fontsize=14, y=1.01)
    plt.subplots_adjust(hspace=0.5)
    plt.tight_layout() 
    # colorbars have to be added after plt.tight_layout() to avoid overlapping with the plot
    for i in color_bars.keys():
        _add_colorbar(axes[i], color_bars[i], colors=colors)
    return fig


def text_dt(classifier, **params):
    return sktree.export_text(classifier, **params)


def text_rf(classifier, **params):
    s = ""
    for i in range(len(classifier.estimators_)):
        s += "\nEstimator: %d\n" % i
        s += sktree.export_text(classifier.estimators_[i], **params)
    return s


VISUALIZATIONS = {
    'DT':  {'image': image_dt, 'text': text_dt},
    'kNN': {'image': image_knn, 'data': True},
    'RF':  {'image': image_rf, 'text': text_rf},
}
for a in ['AC', 'AP', 'Birch', 'DBSCAN', 'KMeans', 'MBKMeans', 'MS', 'OPTICS', 'SC']:
    VISUALIZATIONS[a] = {'image': image_clustering, 'data': True, 'target': True}

