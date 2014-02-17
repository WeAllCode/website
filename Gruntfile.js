module.exports = function(grunt) {
    'use strict';

    // load custom tasks
    grunt.loadNpmTasks('grunt-contrib-watch');
    grunt.loadNpmTasks('grunt-contrib-compass');
    grunt.loadNpmTasks('grunt-contrib-cssmin');
    grunt.loadNpmTasks('grunt-contrib-jshint');
    grunt.loadNpmTasks('grunt-contrib-uglify');

    // initialize the configuration
    grunt.initConfig({
        pkg: grunt.file.readJSON('package.json'),

        files: {
            grunt: 'Gruntfile.js',
            root: 'coderdojochi',
            static: '<%= files.root %>/static',
            templates: '<%= files.root %>templates',
            css: '<%= files.static %>/css',
            sass: '<%= files.static %>/scss',
            js: '<%= files.static %>/js',
            img: '<%= files.static %>/images',
            sprites: '<%= files.static %>/sprites',
            builtJS: '<%= files.static %>/build/js',
            builtCSS: '<%= files.static %>/build/css',
            sourceMap: 'cdc-mobile.min.map'
        },

        watch: {
            scripts: {
                files: [
                    '<%= files.grunt %>',
                    '<%= files.js %>/**/*.js'
                ],
                tasks: ['jshint'],
                options: {
                    livereload: true
                }
            },
            scss: {
                files: ['<%= files.sass %>/**/*.scss'],
                tasks: ['compass:dev']
            },
            markup: {
                files: [
                    '<%= files.templates %>/**/*.html',
                    '**/*.{html,php}'
                ],
                options: {
                    livereload: true
                }
            },
            livereload: {
                files: ['<%= files.css %>/**/*.css'],
                options: {
                    livereload: true
                }
            }
        },

        compass: {
            dist: {
                options: {
                    require: ['susy'],
                    sassDir: '<%= files.sass %>',
                    cssDir: '<%= files.css %>',
                    imagesDir: '<%= files.img %>',
                    raw: 'sprite_load_path = "<%= files.sprites %>"\n',
                    httpGeneratedImagesPath: '../images',
                    environment: 'production',
                    outputStyle: 'compressed',
                    debugInfo: false,
                    noLineComments: true,
                    force: true
                }
            },
            dev: {
                options: {
                    require: ['susy'],
                    sassDir: '<%= files.sass %>',
                    cssDir: '<%= files.css %>',
                    imagesDir: '<%= files.img %>',
                    raw: 'sprite_load_path = "<%= files.sprites %>"\n',
                    httpGeneratedImagesPath: '../images',
                    outputStyle: 'expanded',
                    debugInfo: true
                }
            }
        },

        cssmin: {
            minify: {
                src: [
                    '<%= files.css %>/cdc.css'
                ],
                dest: '<%= files.builtCSS %>/cdc.min.css'
            }
        },

        jshint: {
            files: ['<%= files.js %>/*.js'],
            options: {
                forin: true,
                noarg: true,
                noempty: true,
                eqeqeq: true,
                bitwise: true,
                strict: false,
                undef: false,
                curly: true,
                expr: true,
                browser: true,
                jquery: true,
                devel: true,
                maxerr: 100,
                ignores: [
                    '<%= files.js %>/*.min.js'
                ],
                // ignore certain warnings
                '-W040': true
            }
        },

        uglify: {
            deploy: {
                options: {
                    sourceMap: '<%= files.builtJS %>/<%= files.sourceMap %>',
                    sourceMappingURL: '<%= files.sourceMap %>',
                    mangle: false
                },
                files: {
                    '<%= files.builtJS %>/cdc.min.js': [
                        '<%= files.js %>/vendor/*.js',
                        '<%= files.js %>/*.js'
                    ]
                }
            }
        }
    });

    // default task
    grunt.registerTask('default', ['watch']);
    grunt.registerTask('deploy', ['compass:dist', 'cssmin', 'jshint', 'uglify']);
};
