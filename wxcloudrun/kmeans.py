class KMeans:
    def __init__(self, n_clusters, max_iter=300):
        self.n_clusters = n_clusters
        self.max_iter = max_iter
    def fit(self, data):
        self.centroids = self.initialize_centroids(data)
        for _ in range(self.max_iter):
            clusters = self.assign_clusters(data, self.centroids)
            new_centroids = self.calculate_centroids(data, clusters)
            if self.centroids == new_centroids:
                break
            self.centroids = new_centroids
        self.labels = self.get_labels(data, clusters)
    def predict(self, data):
        return self.labels
    def initialize_centroids(self, data):
        import random
        random.seed(42)
        indices = random.sample(range(len(data)), self.n_clusters)
        return [data[i] for i in indices]
    def assign_clusters(self, data, centroids):
        clusters = {i: [] for i in range(self.n_clusters)}
        for point in data:
            closest_centroid_idx = self.closest_centroid(point, centroids)
            clusters[closest_centroid_idx].append(point)
        return clusters
    def calculate_centroids(self, data, clusters):
        new_centroids = []
        for i, cluster_points in clusters.items():
            cluster_mean = tuple(sum(coord) / len(coord) for coord in zip(*cluster_points))
            new_centroids.append(cluster_mean)
        return new_centroids
    def closest_centroid(self, point, centroids):
        min_dist = float('inf')
        closest_centroid_idx = -1
        for i, centroid in enumerate(centroids):
            dist = sum((a - b) ** 2 for a, b in zip(point, centroid)) ** 0.5
            if dist < min_dist:
                min_dist = dist
                closest_centroid_idx = i
        return closest_centroid_idx
    def get_labels(self, data, clusters):
        labels = []
        for point in data:
            for i, cluster_points in clusters.items():
                if point in cluster_points:
                    labels.append(i)
                    break
        return labels