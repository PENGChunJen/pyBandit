from copy import deepcopy
import numpy as np

from cluster import weighted_gaussian
from OnePlusOne_ES import OnePlusOne_ES

class Matrix:

    def __init__(self, positions, fitnesses, min_bounds, max_bounds, matrix=None):

        self.delta = 1e-08
        self.min_bounds = min_bounds
        self.max_bounds = max_bounds
        self.dimension = len(positions[0])

        if matrix is None:
            self.matrix = self.init_matrix( positions, fitnesses )
        else:
            self.matrix = matrix


    
    def init_matrix(self, positions, fitnesses):

        best = positions[ np.argmin(fitnesses) ]
        mean, cov = weighted_gaussian(positions, fitnesses)

        amax = np.amax(positions, axis = 0) + self.delta
        amin = np.amin(positions, axis = 0) - self.delta
        center = 0.5*(amax + amin)
        transfer = (mean - center) + (best - mean)

        # Elementwise minimum and maximum
        #amax = np.minimum( amax + np.clip(transfer, 0, None), self.max_bounds + self.delta )
        #amin = np.maximum( amin + np.clip(transfer, None, 0), self.min_bounds - self.delta )
        amax = np.minimum( amax + np.clip(transfer, 0, None), self.max_bounds )
        amin = np.maximum( amin + np.clip(transfer, None, 0), self.min_bounds )

        scale = amax - amin
        scale_matrix = np.eye(self.dimension + 1)
        for i in range(self.dimension):
            if scale[i] != 0:
                scale_matrix[i, i] = 1.0 / scale[i]


        translate_matrix = np.eye(self.dimension + 1)
        translate_matrix[:-1, -1] = -(amin.T)

        return np.dot(scale_matrix, translate_matrix)

    
    '''
    def transform_without_clip(self, positions, **kwargs):
        get_original = kwargs.get('get_original', False)
        if len(positions) == 0:
            return []

        positions = np.array(positions)
        positions = np.hstack((positions, np.ones((positions.shape[0], 1))))
        trans_positions = np.dot(self.matrix, positions.T).T

        if not get_original:
            w = trans_positions[:, -1]
            w[w == 0] = self.delta
            trans_positions = trans_positions[:, :-1] / w[:, None]

        # Check all points falls in [0,1]^D subspace
        #trans_positions = np.clip( trans_positions, 0, 1 )
        return trans_positions
    '''

    
    def transform(self, positions, **kwargs):
        get_original = kwargs.get('get_original', False)
        without_clip = kwargs.get('without_clip', False)
        if len(positions) == 0:
            return []

        positions = np.array(positions)
        positions = np.hstack((positions, np.ones((positions.shape[0], 1))))
        trans_positions = np.dot(self.matrix, positions.T).T

        if not get_original:
            w = trans_positions[:, -1]
            w[w == 0] = self.delta
            trans_positions = trans_positions[:, :-1] / w[:, None]

        # Project all points out of [0,1]^D subspace
        # onto a sphere( center = [0.5]^D, r = 0.5 )
        if not without_clip:
            num_points, dimension = trans_positions.shape
            center = 0.5*np.ones(dimension)
            for i, trans_position in enumerate(trans_positions):
                if (trans_position > 1).any() or (trans_position < 0).any():
                    vector = trans_position - center 
                    dist_to_center = np.linalg.norm(vector)
                    vector = (0.5/dist_to_center) * vector
                    trans_positions[i] = center + vector

        return trans_positions


    
    def inverse_transform(self, positions, **kwargs):
        get_original = kwargs.get('get_original', False)
        if len(positions) == 0:
            return []

        positions = np.array(positions)
        positions = np.hstack((positions, np.ones((positions.shape[0], 1))))
        trans_positions = np.dot(np.linalg.inv(self.matrix), positions.T).T

        if not get_original:
            w = trans_positions[:, -1]
            w[w == 0] = self.delta
            trans_positions = trans_positions[:, :-1] / w[:, None]

        return trans_positions



    def optimize(self, include, include_fitnesses, exclude, max_evaluation_num = 100, restart = 3):

        dimension = self.matrix.shape[0] - 1
        n_samples = 100 * dimension 

        # Repeatedly used parameters in evaluate
        #self.original_best_position = deepcopy(best)
        self.original_positions_in  = deepcopy(include)
        self.original_fitnesses_in  = deepcopy(include_fitnesses)
        self.original_positions_out = deepcopy(exclude)
        self.samples = np.random.uniform(0, 1, size=(n_samples, dimension))

        best_solution = self.matrix.ravel()
        best_score = self.evaluate( best_solution )
        #print( 'Init score:', self.evaluate(best_solution, debug=True) )

        # Use (1+1)-ES to optimize matrix
        for _ in range(restart):
            es = OnePlusOne_ES( self.evaluate, len(best_solution), 
                                parent = self.matrix.ravel(),
                                #parent = best_solution, 
                                step = 0.01,
                                max_iteration = max_evaluation_num)
            while not es.stop(): x_best, score = es.run()
            if score < best_score:
                best_score = score
                best_solution = x_best
            #print( 'Final score:', score) 


        self.matrix = np.array(best_solution).reshape( self.matrix.shape )
        #print( 'Final score:', self.evaluate(best_solution, debug=True) )


    def evaluate(self, X, debug=False):
        self.matrix = np.array(X).reshape( self.matrix.shape )

        trans_in   = self.transform(self.original_positions_in, without_clip = True)
        mean, cov = weighted_gaussian(trans_in, self.original_fitnesses_in)

        if self.original_positions_out.any():
            trans_out  = self.transform(self.original_positions_out, without_clip = True)
            trans_out  = trans_out[ np.all( trans_out >= 0, axis=1) ]
            trans_out  = trans_out[ np.all( trans_out <= 1, axis=1) ]


        ori_samples = self.inverse_transform(self.samples)

        out_min_bounds = self.min_bounds - ori_samples
        out_min_bounds = out_min_bounds[ out_min_bounds > 0 ]
        dist_out_min_bounds = sum( out_min_bounds )

        out_max_bounds = ori_samples - self.max_bounds
        out_max_bounds = out_max_bounds[ out_max_bounds > 0 ]
        dist_out_max_bounds = sum( out_max_bounds )


        # Features to be minimized
        dist_mean_to_center = np.linalg.norm( mean - 0.5 )

        normal_cov = 0.25*np.eye(self.dimension)
        dist_cov_to_norm_cov = np.linalg.norm(cov-normal_cov)

        dist_should_be_in   = abs(sum( trans_in[ np.where(trans_in > 1.0) ] - 1.0 ))
        dist_should_be_in  += abs(sum( trans_in[ np.where(trans_in < 0.0) ] ))

        dist_should_be_out = 0 
        if self.original_positions_out.any():
            lower_half = np.where( np.logical_and( trans_out >= 0.0, trans_out < 0.5 ) )
            upper_half = np.where( np.logical_and( trans_out >= 0.5, trans_out <= 1.0 ) )
            dist_should_be_out  = abs(sum( trans_out[ lower_half ] ))
            dist_should_be_out += abs(sum( trans_out[ upper_half ] - 0.5 ))

        

        clipped_trans_in = self.transform(self.original_positions_in, without_clip = False)
        reconstruct = self.inverse_transform( clipped_trans_in )
        reconstruct_error = sum( np.linalg.norm( p1 - p2 ) \
                                 for p1, p2 in zip(reconstruct, self.original_positions_in) )

        score  = 0.0
        score += 100*reconstruct_error 
        # Limit in global boundary
        score += dist_should_be_in 
        score += dist_should_be_out 
        # Split point in and out of cluster
        if dist_should_be_out > 0:
            score += len(trans_out)
        score += dist_out_min_bounds
        score += dist_out_max_bounds
        # Approximate a Normal distribution N(mean, cov) on subspace
        score += dist_mean_to_center
        score += dist_cov_to_norm_cov

        if not debug:
            return score 
        else:
            #print('trans_out:\n', trans_out)
            #print('trans_in:\n', trans_in)
            #print('trans_best:\n', trans_best)
            #print('original:\n', self.original_positions_in)
            #print('reconstruct:\n', reconstruct)
            #if reconstruct_error > 1:
            if True:
                print('dist_in  :', dist_should_be_in)
                print('dist_min :', dist_out_min_bounds)
                print('dist_max :', dist_out_max_bounds)
                print('dist_out :', dist_should_be_out)
                print('dist_best:', dist_best_to_center)
                print('std      :', trans_std)
                print('dist_std :', dist_std)
                print('error    :', reconstruct_error)
                print('score    :', score)
                #print(self.matrix)
                subspace_border = np.array([ [ 0, 0], [ 1, 0], [ 1, 1], [ 0, 1] ])
                border = self.inverse_transform( subspace_border )
                #print(subspace_border)
                #print(border)
                #print()
            return score 
            #return reconstruct_error



if __name__ == '__main__':

    dimension = 2
    n_points = 5 
    function_id = 7

    from optproblems.cec2005 import CEC2005
    from boundary import Boundary
    obj = CEC2005(dimension)[function_id-1].objective_function 
    positions = np.random.uniform(-100, 100, size = (n_points, dimension))
    fitnesses = np.array([obj(x) for x in positions])
    boundary = Boundary(dimension, function_id-1)

    selected = fitnesses.argsort()[:int(len(positions)/2)]
    positions, fitnesses = positions[selected], fitnesses[selected]

    m = Matrix(positions, fitnesses, boundary.min_bounds, boundary.max_bounds)
    #m.matrix = np.random.uniform(boundary.init_min_bounds, boundary.init_max_bounds, 
    #                             size = (dimension+1, dimension+1) )
    X = positions

    print('\nTransformation Matrix:')
    print(m.matrix)
    print('\nInverse Matrix:')
    print(np.linalg.inv(m.matrix))

    print('\noriginal points:')
    print(X)

    print('\ntransformed points:')
    trans_X = m.transform(X, get_original=True) 
    print(trans_X)

    print('\nnormalized transformed points:')
    trans_X = m.transform(X)
    print(trans_X)

    print('\nrestored points:')
    restored_X = m.inverse_transform(trans_X, get_original=True) 
    print(restored_X)
        
    print('\nnormalized restored points:')
    restored_X = m.inverse_transform(trans_X) 
    print(restored_X)
    
