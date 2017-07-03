from copy import deepcopy
from operator import attrgetter
from scipy.optimize import fmin_tnc
from scipy.stats import chisqprob, multivariate_normal
import numpy as np 

from OnePlusOne_ES import OnePlusOne_ES
from CMAES import CMA
from SPSO2011 import PSO
from ACOR import ACOR
from matrix import Matrix
from cluster import weighted_gaussian, manhalanobis_distance        


class Arm:
    def __init__(self, obj, n_points, init_positions, init_fitnesses, 
                 algo_type='CMA', exclude=None, matrix=None, **kwargs ):

        self.obj = obj
        self.n_points = n_points
        self.dimension = len(init_positions[0])
        self.n_samples = 100 * self.dimension
        self.algo_type = algo_type
        self.min_bounds = kwargs.get('min_bounds', np.array([0.0] * self.dimension))
        self.max_bounds = kwargs.get('max_bounds', np.array([1.0] * self.dimension))

        self.evaluation_num = 0
        self.max_evaluation_num = 10000


        if matrix is None:
            # Optimize transformation matrix
            best_index = np.argmin( init_fitnesses )
            best_position = init_positions[best_index] 

            self.matrix = Matrix(init_positions)
            self.matrix.optimize( best_position, 
                                  init_positions, 
                                  exclude, 
                                  self.min_bounds,
                                  self.max_bounds,
                                  max_evaluation_num = 10000 ) 
        else:
            self.matrix = matrix
        
        # Resize population == n_points
        positions, fitnesses = self.resize_population( init_positions, init_fitnesses )
        self.mean, self.cov = weighted_gaussian( positions, fitnesses )

        # Transform points onto subspace
        trans_positions = self.matrix.transform(positions) 

        # Check boundary is in 0, 1
        trans_positions = np.clip( trans_positions, 0, 1 )

        # Initialize algorithm
        self.init_algo( trans_positions, fitnesses ) 


    def update_model(self):
        self.mean, self.cov = weighted_gaussian( self.get_positions(), self.get_fitnesses() ) 


    def resize_population(self, init_positions, init_fitnesses):
        if len(init_positions) > self.n_points:
            # Select top n_points to initialize algorithm
            index = init_fitnesses.argsort()
            selected = index[:self.n_points]
            positions, fitnesses = init_positions[selected], init_fitnesses[selected]
        elif len(init_positions) == self.n_points:
            positions, fitnesses = init_positions, init_fitnesses
        else:
            # Add points until population == n_points
            add_n = self.n_points - len(init_positions)
            subspace_positions = np.random.uniform( 0.0, 1.0, size=(add_n, self.dimension) )
            new_positions = self.matrix.inverse_transform( subspace_positions )
            new_fitnesses = np.array( [self.obj(p) for p in new_positions] )

            positions = np.concatenate((init_positions, new_positions), axis=0)
            fitnesses = np.concatenate((init_fitnesses, new_fitnesses), axis=0)
            index = fitnesses.argsort()
            positions, fitnesses = positions[index], fitnesses[index]

        return positions, fitnesses



    def init_algo(self, init_positions, init_fitnesses ):
        if self.algo_type == 'PSO':
            self.algo = PSO(self.transform_obj, self.n_points, self.dimension, 
                            init_positions=init_positions, 
                            init_fitnesses=init_fitnesses )
        elif self.algo_type=='ACOR':
            self.algo = ACOR(self.transform_obj, self.dimension, 
                             ants_num = 2,
                             archive_size = self.n_points, # 50
                             q = 1e-4, #1e-4, 0.1, 0.3, 0.5, 0.9
                             xi = 0.85, 
                             init_positions=init_positions, 
                             init_fitnesses=init_fitnesses )
        else:
            self.algo = CMA(self.transform_obj, self.n_points, self.dimension, 
                            init_positions=init_positions, 
                            init_fitnesses=init_fitnesses )



    def transform_obj(self, X):
        original_X = self.matrix.inverse_transform([X])[0]
        return self.obj(original_X)



    def pull(self):
        #best_position, best_fitness = self.algo.run() 
        best_position, best_fitness = self.algo.update_one_particle()
        return self.matrix.inverse_transform([best_position])[0], best_fitness



    def transform(self, new_matrix):
        self.algo.transform( self.matrix, new_matrix )
        self.matrix = deepcopy(new_matrix)



    def draw(self, ax, color, on_subspace=False):

        # Plot borders on original search space
        border = np.array([ [ 0, 0], [ 1, 0], [ 1, 1], [ 0, 1], [ 0, 0]])
        if not on_subspace:
            border = self.matrix.inverse_transform( border )
        ax.plot(border[:, 0], border[:, 1], color = color)

        # Plot algorithm
        if not on_subspace:
            self.algo.draw( ax, color, self.matrix )
        else:
            self.algo.draw( ax, color )


    def reject_model(self):

        original_positions = self.get_positions()
        original_fitnesses = self.get_fitnesses()
        '''
        from cluster import clustering
        labels = clustering( original_positions, original_fitnesses )
        if any(labels) > 0:
            print(labels)
        return any(labels) > 0
        '''    

        mean, cov = weighted_gaussian( original_positions, original_fitnesses )
        wilks_statistics = self.n_points * manhalanobis_distance( mean, self.mean, self.cov )
        dof = self.dimension
        p_value = chisqprob( wilks_statistics, dof )
        if p_value < 0.05:
            print('\nReject_model: p_value:%f, mean:'%p_value, mean, self.mean )

        return p_value < 0.05

    # Should DELETE
    ########################################################################
    def reached_border(self, r = 0.25):
        #'''
        r = 0.3536
        trans_positions = self.algo.get_positions()
        best_index = np.argmax(self.algo.get_fitnesses())  
        trans_best_position = trans_positions[best_index]
        dist_best_to_center = np.linalg.norm( trans_best_position - 0.5 )
        if dist_best_to_center > r:
            best_position = self.matrix.inverse_transform([trans_best_position])[0]
            print(best_position, trans_best_position, dist_best_to_center)
        return (dist_best_to_center > r)
        #'''

        margin = 0.10

        trans_positions = self.algo.get_positions()
        trans_mean_position = np.mean(trans_positions, axis=0)

        best_index = np.argmax(self.algo.get_fitnesses())  
        trans_best_position = trans_positions[best_index]

        if ((trans_best_position < margin).any() or (trans_best_position > 1.0-margin).any()) and \
           ((trans_mean_position < 2.0*margin).any() or (trans_mean_position > 1.0-2.0*margin).any()):
            return True
        return False
    ########################################################################


    def translate_to(self, original_best_position):
    
        positions = deepcopy(self.get_positions())
        fitnesses = self.get_fitnesses()

        center = self.matrix.inverse_transform( [[0.5]*self.dimension] )[0]

        translate = center - original_best_position 
        translate_matrix = np.eye( self.dimension + 1 ) 
        translate_matrix[:-1, -1] = translate.T

        self.matrix.matrix = np.dot( self.matrix.matrix, translate_matrix )

        trans_positions = self.matrix.transform(positions) 
        trans_positions = np.clip( trans_positions, 0, 1 )
        assert (trans_positions.all() >= 0) and (trans_positions.all() <= 1)

        self.init_algo( trans_positions, fitnesses )



    def get_positions(self):
        return self.matrix.inverse_transform( self.algo.get_positions() )
    def get_fitnesses(self):
        return self.algo.get_fitnesses()


    def stop(self):
        return self.algo.stop()

    

    # Should Remove...
    def update_matrix(self, best, include, exclude):


        # Repeatedly used parameters in evaluate
        self.original_best_position = deepcopy(best)
        self.original_positions_in  = deepcopy(include)
        self.original_positions_out = deepcopy(exclude)
        self.samples = np.random.uniform(0, 1,
                                         size=(self.n_samples, self.dimension))

        best_solution = self.matrix.matrix.ravel()
        best_score = self.evaluate( best_solution )
        #print( 'Init score:', self.evaluate(best_solution, debug=True) )


        '''
        # Newton Conjugate-Gradient algorithm
        self.evaluation_num = 0
        while self.evaluation_num < self.max_evaluation_num:
            solution = best_solution + np.random.uniform( -1e-3, 1e-3, size=best_solution.shape )
            #print( 'Init score:', self.evaluate(solution) )
            res = fmin_tnc(self.evaluate, solution, approx_grad=True, maxfun=1000, disp=0)
            #res = fmin_tnc(self.evaluate, solution, approx_grad=True, maxfun=1000 )
            x_best = res[0]
            score = self.evaluate( x_best )
            if score < best_score:
                best_score = score
                best_solution = x_best
            #print( 'Final score:', score) 

        '''

        '''
        # CMA-ES
        import cma
        es = cma.CMAEvolutionStrategy( best_solution.tolist(), 1e-4, 
                                       {'maxiter': self.max_evaluation_num} )

        while not es.stop():
            solutions = es.ask()
            es.tell( solutions, [self.evaluate(s) for s in solutions] )
            x_best = es.result()[0]
            score = self.evaluate( x_best )
            if score < best_score:
                best_score = score
                best_solution = x_best
            #print( 'Final score:', score) 
        '''
        repeat = 20
        for _ in range(repeat):
            es = OnePlusOne_ES( self.evaluate, len(best_solution), 
                                parent = self.matrix.matrix.ravel(),
                                #parent = best_solution, 
                                step = 0.1,
                                max_iteration = self.max_evaluation_num / repeat )
            while not es.stop():
                x_best, score = es.run()
            if score < best_score:
                best_score = score
                best_solution = x_best
            #print( 'Final score:', score) 


        self.matrix.matrix = np.array(best_solution).reshape( self.matrix.matrix.shape )
        #print( 'Final score:', self.evaluate(best_solution, debug=True) )


    def evaluate(self, X, debug=False):
        self.evaluation_num += 1
        self.matrix.matrix = np.array(X).reshape( self.matrix.matrix.shape )

        trans_best = self.matrix.transform([self.original_best_position])[0]
        
        trans_in   = self.matrix.transform(self.original_positions_in)

        if self.original_positions_out.any():
            trans_out  = self.matrix.transform(self.original_positions_out)
            trans_out  = trans_out[ np.all( trans_out >= 0, axis=1) ]
            trans_out  = trans_out[ np.all( trans_out <= 1, axis=1) ]


        ori_samples = self.matrix.inverse_transform(self.samples)

        out_min_bounds = self.min_bounds - ori_samples
        out_min_bounds = out_min_bounds[ out_min_bounds > 0 ]
        dist_out_min_bounds = sum( out_min_bounds )

        out_max_bounds = ori_samples - self.max_bounds
        out_max_bounds = out_max_bounds[ out_max_bounds > 0 ]
        dist_out_max_bounds = sum( out_max_bounds )


        # Features to be minimized
        dist_best_to_center = np.linalg.norm( trans_best - 0.5 )

        dist_should_be_in   = abs(sum( trans_in[ np.where(trans_in > 1.0) ] - 1.0 ))
        dist_should_be_in  += abs(sum( trans_in[ np.where(trans_in < 0.0) ] ))

        dist_should_be_out = 0 
        if self.original_positions_out.any():
            lower_half = np.where( np.logical_and( trans_out >= 0.0, trans_out < 0.5 ) )
            upper_half = np.where( np.logical_and( trans_out >= 0.5, trans_out <= 1.0 ) )
            dist_should_be_out  = abs(sum( trans_out[ lower_half ] ))
            dist_should_be_out += abs(sum( trans_out[ upper_half ] - 0.5 ))

        
        reconstruct = self.matrix.inverse_transform( np.clip(trans_in, 0, 1) )
        reconstruct_error = sum( np.linalg.norm( p1 - p2 ) \
                                 for p1, p2 in zip(reconstruct, self.original_positions_in) )

        trans_std = np.std( (trans_in - trans_best), axis=0 )
        dist_std = sum( abs(trans_std - 0.3) ) 
        

        score  = 0.0
        score += 100*reconstruct_error 
        # Limit in global boundary
        score += dist_should_be_in 
        score += dist_should_be_out 
        # Split point in and out of cluster
        score += dist_out_min_bounds
        score += dist_out_max_bounds
        # Approximate a Normal distribution centering at trans_best
        score += dist_best_to_center
        score += dist_std

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
                #print(self.matrix.matrix)
                subspace_border = np.array([ [ 0, 0], [ 1, 0], [ 1, 1], [ 0, 1] ])
                border = self.matrix.inverse_transform( subspace_border )
                #print(subspace_border)
                #print(border)
                #print()
            return score 
            #return reconstruct_error




def draw_arms(function_id, arms, **kwargs):

    import os
    from optproblems.cec2005 import CEC2005
    import matplotlib.pyplot as plt
    from matplotlib import cm
    from boundary import Boundary

    # Parameters
    dim = 2
    function = CEC2005(dim)[function_id].objective_function
    optimal_pos = CEC2005(dim)[function_id].get_optimal_solutions()[0].phenome
    boundary = Boundary(dim, function_id)
    plot_subspace = False

    inch_size = 4
    k = len(arms)
    fig_w = (k + 1) if plot_subspace else 1.2
    fig_h = 1
    fig = plt.figure(figsize = (fig_w * inch_size, fig_h * inch_size))
    cmap = cm.coolwarm
    scatter_cmap = cm.jet(np.linspace(0.1, 0.9, k))
    angle = kwargs.get('angle', 240)
    rotate = kwargs.get('rotate', False)
    fig_name = kwargs.get('fig_name', None)
    fig_title = kwargs.get('fig_title', 'F%d'%(function_id+1))
    fig_dir = kwargs.get('fig_dir', 'test_arms')
    if not os.path.exists(fig_dir):
        os.makedirs(fig_dir)

    print('ploting %s...' % fig_name)

    # Plot contour
    ax = fig.add_subplot(fig_h, fig_w, 1)

    # Get Mesh Solutions for contour
    step = (boundary.max_bounds[0] - boundary.min_bounds[0]) / 100
    X = np.arange(boundary.min_bounds[0], boundary.max_bounds[0] + step, step)
    Y = np.arange(boundary.min_bounds[1], boundary.max_bounds[1] + step, step)
    (X, Y) = np.meshgrid(X, Y)
    positions = [ [x, y] for x, y in zip(X.ravel(), Y.ravel()) ]
    Z = np.array( [ function(position) for position in positions ] )

    # Reset colormap to get rid of extreme colors
    v_range = max(Z) - min(Z)
    vmin = min(Z) - v_range * 0.2
    vmax = max(Z) + v_range * 0.2
    Z = Z.reshape(X.shape)

    #margin = (boundary.max_bounds - boundary.min_bounds)*0.1
    margin = (boundary.max_bounds - boundary.min_bounds)*0.0
    ax.set_xlim([ boundary.min_bounds[0] - margin[0], boundary.max_bounds[0] + margin[0] ])
    ax.set_ylim([ boundary.min_bounds[1] - margin[1], boundary.max_bounds[1] + margin[1] ])
    cset = ax.contourf(X, Y, Z, cmap = cmap, vmin = vmin, vmax = vmax)
    fig.colorbar(cset, aspect = 20)

    # Plot optimal solution as a big white 'X'
    ax.scatter(optimal_pos[0], optimal_pos[1], color = 'w', marker = 'x', s = 100)


    # Plot scatter points in each arm
    colors = iter(scatter_cmap)
    for arm in arms:
        arm.draw( ax, next(colors), on_subspace=False )



    if plot_subspace:
        # Plot from each arm's perspective
        for i, arm in enumerate(arms):

            color = scatter_cmap[i]
            ax_sub = fig.add_subplot(fig_h, fig_w, i + 2)
            ax_sub.set_xlim([ -0.01, 1.01])
            ax_sub.set_ylim([ -0.01, 1.01])

            # Plot contour
            (X, Y) = np.meshgrid( np.arange(0, 1.01, 0.01), np.arange(0, 1.01, 0.01) )

            mesh_positions = [ [x, y] for x, y in zip(X.ravel(), Y.ravel())]
            original_positions = arm.matrix.inverse_transform(mesh_positions)

            Z = np.array( [ function(mesh_position) for mesh_position in original_positions ] )
            Z = Z.reshape(X.shape)

            cset = ax_sub.contourf(X, Y, Z, cmap = cmap, vmin = vmin, vmax = vmax)


            # Plot scatter points in each arm
            arm.draw( ax_sub, color, on_subspace=True )


    fig.tight_layout()
    st = fig.suptitle(fig_title, fontsize = 16)
    st.set_y(0.95)
    fig.subplots_adjust(top = 0.85)
    if fig_name is not None:
        plt.savefig( '%s/%s' % (fig_dir,fig_name) )
    else:
        plt.show()
        input('Press Enter to continue...')
    plt.close(fig)





def draw_optimization(function_id, cluster_positions, matrices, **kwargs):

    assert len(cluster_positions) == len(matrices)
    import os
    from optproblems.cec2005 import CEC2005
    import matplotlib.pyplot as plt
    from matplotlib import cm
    from boundary import Boundary

    # Parameters
    dim = 2
    function = CEC2005(dim)[function_id].objective_function
    optimal_pos = CEC2005(dim)[function_id].get_optimal_solutions()[0].phenome
    boundary = Boundary(dim, function_id)

    k = len(matrices)
    inch_size = 4
    #fig_w = k + 1
    fig_w = 1.2
    fig_h = 1
    fig = plt.figure(figsize = (fig_w * inch_size, fig_h * inch_size))
    cmap = cm.coolwarm
    scatter_cmap = cm.jet(np.linspace(0.1, 0.9, k))
    angle = kwargs.get('angle', 240)
    rotate = kwargs.get('rotate', False)
    fig_name = kwargs.get('fig_name', None)
    fig_title = kwargs.get('fig_title', 'F%d'%(function_id+1))
    fig_dir = kwargs.get('fig_dir', 'test_arms')
    if not os.path.exists(fig_dir):
        os.makedirs(fig_dir)

    print('ploting %s...' % fig_name)


    # Get Mesh Solutions for contour
    step = (boundary.max_bounds[0] - boundary.min_bounds[0]) / 100
    X = np.arange(boundary.min_bounds[0], boundary.max_bounds[0] + step, step)
    Y = np.arange(boundary.min_bounds[1], boundary.max_bounds[1] + step, step)
    (X, Y) = np.meshgrid(X, Y)
    positions = [ [x, y] for x, y in zip(X.ravel(), Y.ravel()) ]
    Z = np.array( [ function(position) for position in positions ] )

    # Reset colormap to get rid of extreme colors
    vmin = min(Z)
    vmax = max(Z)
    vmin = vmin - (vmax - vmin) * 0.2
    vmax = vmax + (vmax - vmin) * 0.2
    Z = Z.reshape(X.shape)

    # Plot contour
    ax = fig.add_subplot(fig_h, fig_w, 1)
    #margin = (boundary.max_bounds - boundary.min_bounds)*0.1
    margin = (boundary.max_bounds - boundary.min_bounds)*0.0
    ax.set_xlim([ boundary.min_bounds[0] - margin[0], boundary.max_bounds[0] + margin[0] ])
    ax.set_ylim([ boundary.min_bounds[1] - margin[1], boundary.max_bounds[1] + margin[1] ])
    cset = ax.contourf(X, Y, Z, cmap = cmap, vmin = vmin, vmax = vmax)
    fig.colorbar(cset, aspect = 20)


    # Plot scatter points in each arm
    colors = iter(scatter_cmap)
    for positions, matrix in zip(cluster_positions, matrices):
        color = next(colors)
        ax.scatter(positions[:,0], positions[:,1], color = color, marker = 'o', s = 10)

        # Plot borders on original boundary
        subspace_border = np.array([ [ 0, 0], [ 1, 0], [ 1, 1], [ 0, 1], [ 0, 0]])
        border = matrix.inverse_transform( subspace_border )
        ax.plot(border[:, 0], border[:, 1], color = color)
    
    # Plot optimal solution as a big white 'X'
    ax.scatter(optimal_pos[0], optimal_pos[1], color = 'w', marker = 'x', s = 100)

    '''
    # Plot from each arm's perspective
    for i, (positions, matrix) in enumerate(zip(cluster_positions, matrices)):
        color = scatter_cmap[i]
        ax = fig.add_subplot(fig_h, fig_w, i + 2)
        ax.set_xlim([ -0.01, 1.01])
        ax.set_ylim([ -0.01, 1.01])
        # Plot contour
        (X, Y) = np.meshgrid( np.arange(0, 1.01, 0.01), np.arange(0, 1.01, 0.01) )
        mesh_positions = [ [x, y] for x, y in zip(X.ravel(), Y.ravel())]
        original_positions = matrix.inverse_transform(mesh_positions)
        Z = np.array( [ function(mesh_position) for mesh_position in original_positions ] )
        Z = Z.reshape(X.shape)
        cset = ax.contourf(X, Y, Z, cmap = cmap, vmin = vmin, vmax = vmax)
        # Plot scatter points in each arm
        trans_X = matrix.transform( positions )
        ax.scatter(trans_X[:, 0], trans_X[:, 1], color = color, marker = 'o', s = 10)
        # Plot border
        cord = np.array([ [0, 0], [1, 0], [1, 1], [0, 1]])
        ax.plot(cord[[0, 1, 2, 3, 0], 0], cord[[0, 1, 2, 3, 0], 1], color = color)
    ''' 

    fig.tight_layout()
    st = fig.suptitle(fig_title, fontsize = 16)
    st.set_y(0.95)
    fig.subplots_adjust(top = 0.85)
    if fig_name is not None:
        plt.savefig( '%s/%s' % (fig_dir,fig_name) )
    else:
        plt.show()
        input('Press Enter to continue...')
    plt.close(fig)


def testArm(plot=False):

    from optproblems.cec2005 import CEC2005
    from sklearn.cluster import KMeans
    from boundary import Boundary

    function_id = 12
    dimension = 2 
    n_points = 12 
    init_num_points = 120
    n_sample = 100 * dimension
    k = 3
    function = CEC2005(dimension)[function_id].objective_function
    init_min_bounds = Boundary(dimension, function_id).init_min_bounds
    init_max_bounds = Boundary(dimension, function_id).init_max_bounds
    min_bounds = Boundary(dimension, function_id).min_bounds
    max_bounds = Boundary(dimension, function_id).max_bounds

    init_positions = np.random.uniform(init_min_bounds[0], 
                                       init_max_bounds[0], 
                                       size=(init_num_points, dimension))
    init_fitnesses = np.array([function(p) for p in init_positions])

    index = init_fitnesses.argsort()
    selected = index[:int(init_num_points/2)]
    positions, fitnesses = init_positions[selected], init_fitnesses[selected]
    labels = KMeans( n_clusters=k ).fit_predict(positions)


    it = 0
    should_terminate = False


    arms = []
    for i in range(k):
        indices = np.where(labels==i)[0]
        arm = Arm( function,
                   n_points,
                   positions[indices],
                   fitnesses[indices],
                   algo_type='PSO',
                   exclude = [],
                   matrix = Matrix( positions[indices] ),
                   min_bounds = min_bounds,
                   max_bounds = max_bounds
                  )
        arms.append(arm)

    if plot: draw_arms( function_id, arms, fig_name='initialize.png' )



    trans_samples = np.random.uniform(0, 1, size=(n_sample, dimension))
    for i in range(k):

        indices = np.where(labels==i)[0]
        argmax = np.argmax( fitnesses[indices] ) 
        best = positions[indices][argmax]

        opt_points = []
        exclude = []
        for j in range(k):
            if i != j: 
                samples = arms[j].matrix.inverse_transform( trans_samples )
                exclude.extend( samples )
                opt_points.append( samples )
            else:
                opt_points.append(positions[indices])

        exclude = np.array(exclude)


        print('optimizing matrix of arm %d ...' % i )
        arms[i].matrix.optimize( best, 
                                 positions[indices], 
                                 exclude, 
                                 min_bounds,
                                 max_bounds,
                                 max_evaluation_num = 1e4 ) 

        if plot: draw_optimization( function_id, 
                                    opt_points,
                                    [arm.matrix for arm in arms],
                                    fig_name='optimize_%d.png'%i )

    if plot: draw_arms( function_id, arms, fig_name='optimized.png' )



    new_matrix = deepcopy(arms[0].matrix)
    translate = np.array([[1,0,-0.5],
                          [0,1,0.5],
                          [0,0,1]])
    new_matrix.matrix = np.dot(new_matrix.matrix, translate) 
    arms[0].transform(new_matrix) 
    if plot: draw_arms( function_id, arms, fig_name='transformed.png' )
     

    '''
    best_fitness = np.inf
    best_position = None

    while not should_terminate:
        should_terminate = True
        for i, arm in enumerate(arms):
            if not arm.stop():
                should_terminate = False
                it += 1

                position, fitness = arm.pull()
                if fitness < best_fitness:
                    best_position, best_fitness = position, fitness

                # TODO
                if arm.reached_border():
                    if plot: 
                        draw_arms( function_id, 
                                   [ arm.get_positions() for arm in arms ],
                                   [ arm.matrix for arm in arms ],
                                   fig_name='it_%d_before_translate.png' % it )

                    ######################################################
                    #positions = arm.get_positions()
                    #fitnesses = arm.get_fitnesses()
                    #best = positions[ np.argmin(fitnesses) ]
                    #if not (position == best).all():
                    #    print(fitness, position)
                    #    print(np.amin(fitnesses), best)
                    #    print()
                    #    for f, p in zip(fitnesses, positions):
                    #        print(f, p)
                    #    input()
                    ######################################################
                    
                    arm.translate_to( position )

                    if plot: 
                        draw_arms( function_id, 
                                   [ arm.get_positions() for arm in arms ],
                                   [ arm.matrix for arm in arms ],
                                   fig_name='it_%d_after_translate.png' % it )


                    exclude = []
                    for j in range(len(arms)):
                        if j != i: 
                            samples = opt_matrices[j].inverse_transform( trans_samples )
                            exclude.extend( samples )

                    # Optimize transformation matrix
                    arm.update_matrix(position, arm.get_positions(), exclude)

                    if plot: 
                        draw_arms( function_id, 
                                   [ arm.get_positions() for arm in arms ],
                                   [ arm.matrix for arm in arms ],
                                   fig_name='it_%d_optimized_translate.png' % it )



                #print('Iter', it, best_fitness, best_position)


    print('Iter', it, best_fitness, best_position)
    if plot: 
        draw_arms( function_id, 
                   [ arm.get_positions() for arm in arms ],
                   [ arm.matrix for arm in arms ],
                   fig_name='it_%d.png' % it )
    '''

if __name__ == '__main__':
    #testArm()
    testArm(plot=True)
    #for i in range(100):
    #    testArm()
